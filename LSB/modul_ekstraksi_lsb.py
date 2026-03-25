import os
import time
import struct
from PIL import Image
from crypt import AESCipher


def info_line(label, value, width=34):
	return f"{label:<{width}}: {value}\n"


def assemble(bits):
	bytes_out = b""
	length = len(bits)
	for idx in range(0, len(bits) // 8):
		byte = 0
		for i in range(0, 8):
			if idx * 8 + i < length:
				byte = (byte << 1) + bits[idx * 8 + i]
		bytes_out += bytes([byte])

	payload_size = struct.unpack("i", bytes_out[:4])[0]
	return bytes_out[4: payload_size + 4]


def read_key_file(key_path):
	with open(key_path, "r", encoding="utf-8") as f:
		lines = [line.strip() for line in f.readlines() if line.strip()]

	key_hex = lines[0].split(":", 1)[1]
	total_bits = int(lines[1].split(":", 1)[1])
	return key_hex, total_bits


def read_coords_file(coords_path):
	with open(coords_path, "r", encoding="utf-8") as f:
		coord_lines = [line.strip() for line in f.readlines() if line.strip()]

	if coord_lines and coord_lines[0].lower().startswith("y,x,channel"):
		return coord_lines[1:]
	return coord_lines


def read_stego_pixels(stego_path):
	img = Image.open(stego_path)
	rgb = img.convert("RGB")
	width, height = img.size
	return rgb.load(), width, height


def extract_bits_with_coords(px, coords, total_bits):
	bits = []
	for row in coords:
		if len(bits) >= total_bits:
			break

		parts = row.split(",")
		if len(parts) != 3:
			continue

		y = int(parts[0])
		x = int(parts[1])
		ch = parts[2].strip().upper()

		r, g, b = px[x, y]
		if ch == "R":
			bits.append(r & 1)
		elif ch == "G":
			bits.append(g & 1)
		elif ch == "B":
			bits.append(b & 1)

	return bits


def extract_bits_blind(px, width, height, total_bits, channel_order=("R", "G", "B")):
	bits = []
	for y in range(height):
		for x in range(width):
			r, g, b = px[x, y]
			values = {"R": r, "G": g, "B": b}
			for ch in channel_order:
				if len(bits) >= total_bits:
					return bits
				bits.append(values[ch] & 1)
	return bits


def bits_to_bitstream(bits):
	return ''.join(str(b) for b in bits)


def bitstream_to_hex(bitstream):
	full_bits = (len(bitstream) // 8) * 8
	bitstream_valid = bitstream[:full_bits]
	data_bytes = bytearray()
	for i in range(0, full_bits, 8):
		data_bytes.append(int(bitstream_valid[i:i + 8], 2))
	return bytes(data_bytes).hex(), full_bits


def calculate_ber(bits_legit, bits_other):
	n = min(len(bits_legit), len(bits_other))
	if n == 0:
		return {"n": 0, "error_bits": 0, "ber_ratio": 0.0, "ber_percent": 0.0}

	error_bits = sum(1 for i in range(n) if bits_legit[i] != bits_other[i])
	ber_ratio = error_bits / n
	return {
		"n": n,
		"error_bits": error_bits,
		"ber_ratio": ber_ratio,
		"ber_percent": ber_ratio * 100.0,
	}


def format_ciphertext_block(title, bits):
	bitstream = bits_to_bitstream(bits)
	ciphertext_hex, valid_bits = bitstream_to_hex(bitstream)
	return (
		f"=== {title} ===\n"
		+ info_line("Panjang bitstream", len(bitstream))
		+ info_line("Bit valid untuk byte", valid_bits)
		+ info_line("Panjang ciphertext hex", len(ciphertext_hex))
		+ "\n"
		+ "[CIPHERTEXT_HEX_UTUH]\n"
		+ f"{ciphertext_hex}\n"
		+ "\n"
		+ "[BITSTREAM_UTUH]\n"
		+ f"{bitstream}\n"
	)


def analyze_plaintext_readability(data):
	if not data:
		return 0.0
	printable = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
	return printable / len(data)


def extract_normal_mode(stego_path, key_path, coords_path, out_file, report_file):
	start_time = time.time()

	key_hex, total_bits = read_key_file(key_path)
	coords = read_coords_file(coords_path)
	px, _, _ = read_stego_pixels(stego_path)

	bits_legit = extract_bits_with_coords(px, coords, total_bits)
	if len(bits_legit) < total_bits:
		print(f"[!] Peringatan: bit terkumpul {len(bits_legit)} < target {total_bits}")

	bits_for_decode = bits_legit.copy()
	if len(bits_for_decode) % 8 != 0:
		bits_for_decode.extend([0] * (8 - (len(bits_for_decode) % 8)))

	data_out = assemble(bits_for_decode)
	cipher = AESCipher(key_hex)
	data_dec = cipher.decrypt(data_out)

	with open(out_file, "wb") as f:
		f.write(data_dec)

	hasil_ber = calculate_ber(bits_legit, bits_legit)

	report = (
		"=== LAPORAN BER NORMAL EXTRACTION ===\n"
		+ info_line("Total bit target (TOTAL_BITS)", total_bits)
		+ info_line("Bit terkumpul legitimate", len(bits_legit))
		+ info_line("n bit yang dibandingkan", hasil_ber["n"])
		+ info_line("Jumlah bit salah", hasil_ber["error_bits"])
		+ info_line("BER (rasio)", f"{hasil_ber['ber_ratio']:.6f}")
		+ info_line("BER (%)", f"{hasil_ber['ber_percent']:.4f}%")
		+ "\n"
		+ format_ciphertext_block("RINGKASAN CIPHERTEXT LEGITIMATE", bits_legit)
		+ "\n"
		+ "Catatan\n"
		+ "BER normal dihitung terhadap dirinya sendiri sebagai baseline, target 0%.\n"
	)

	with open(report_file, "w", encoding="utf-8") as f:
		f.write(report)

	elapsed = time.time() - start_time
	print(f"[V] Normal extract sukses: {out_file}")
	print(f"[V] Laporan normal: {report_file}")
	print(f"[V] BER normal: {hasil_ber['ber_percent']:.4f}%")
	print(f"[V] Waktu extract normal: {elapsed:.4f} detik")
	return elapsed


def extract_blind_mode(stego_path, key_path, coords_path, report_file, blind_output_file):
	start_time = time.time()

	key_hex, total_bits = read_key_file(key_path)
	coords = read_coords_file(coords_path)
	px, width, height = read_stego_pixels(stego_path)

	bits_legit = extract_bits_with_coords(px, coords, total_bits)
	bits_blind = extract_bits_blind(px, width, height, total_bits, channel_order=("R", "G", "B"))

	hasil_ber = calculate_ber(bits_legit, bits_blind)

	blind_status = "GAGAL_UNPADDING_ATAU_FORMAT"
	blind_note = ""

	try:
		bits_for_decode = bits_blind.copy()
		if len(bits_for_decode) % 8 != 0:
			bits_for_decode.extend([0] * (8 - (len(bits_for_decode) % 8)))

		data_out_blind = assemble(bits_for_decode)
		cipher = AESCipher(key_hex)
		data_dec_blind = cipher.decrypt(data_out_blind)

		readability = analyze_plaintext_readability(data_dec_blind)
		if readability >= 0.95:
			cat = "kemungkinan terbaca (tetap perlu verifikasi manual)"
		else:
			cat = "kemungkinan tidak bermakna/noise"

		blind_status = "BERHASIL_SECARA_TEKNIS"
		blind_note = f"Dekripsi blind berhasil. Skor keterbacaan={readability:.4f} ({cat})."

		with open(blind_output_file, "wb") as f:
			f.write(data_dec_blind)
	except Exception as e:
		blind_note = f"Dekripsi blind gagal: {e}"

	report = (
		"=== LAPORAN BER BLIND EXTRACTION ===\n"
		+ info_line("Total bit target (TOTAL_BITS)", total_bits)
		+ info_line("Bit legitimate", len(bits_legit))
		+ info_line("Bit blind", len(bits_blind))
		+ info_line("n bit yang dibandingkan", hasil_ber["n"])
		+ info_line("Jumlah bit salah", hasil_ber["error_bits"])
		+ info_line("BER (rasio)", f"{hasil_ber['ber_ratio']:.6f}")
		+ info_line("BER (%)", f"{hasil_ber['ber_percent']:.4f}%")
		+ "\n"
		+ format_ciphertext_block("RINGKASAN CIPHERTEXT LEGITIMATE", bits_legit)
		+ "\n"
		+ format_ciphertext_block("RINGKASAN CIPHERTEXT BLIND", bits_blind)
		+ "\n"
		+ "=== UJI DEKRIPSI BLIND DENGAN AES_KEY ASLI ===\n"
		+ info_line("Status dekripsi blind", blind_status)
		+ info_line("Catatan", blind_note)
		+ "\n"
		+ "Catatan\n"
		+ "BER blind dihitung dengan XOR per-bit antara ciphertext legitimate extraction dan ciphertext blind extraction.\n"
	)

	with open(report_file, "w", encoding="utf-8") as f:
		f.write(report)

	elapsed = time.time() - start_time
	print(f"[V] Blind extract selesai.")
	print(f"[V] Laporan blind: {report_file}")
	print(f"[V] BER blind: {hasil_ber['ber_percent']:.4f}%")
	print(f"[V] Status dekripsi blind: {blind_status}")
	if blind_status == "BERHASIL_SECARA_TEKNIS":
		print(f"[V] Hasil dekripsi blind: {blind_output_file}")
	print(f"[V] Waktu extract blind: {elapsed:.4f} detik")
	return elapsed
