import cv2
import time
from cvzone.HandTrackingModule import HandDetector

# ==========================================
# FUNGSIONALITAS BINGKAI PHOTOBOOTH
# ==========================================
def apply_photobooth_frame(img, effect_name="NORMAL"):
    """Menambahkan bingkai putih khas photobooth beserta teks cetakan."""
    top, left, right = 30, 30, 30
    bottom = 120  # Ruang ekstra di bawah untuk teks photobooth
    
    # Buat border putih di sekeliling gambar
    framed = cv2.copyMakeBorder(
        img, top, bottom, left, right, 
        cv2.BORDER_CONSTANT, value=[255, 255, 255]
    )
    
    h, w, _ = framed.shape
    
    # Teks Judul Photobooth (Warna Abu Gelap)
    cv2.putText(framed, "RUBU PHOTO", (left + 10, h - 65),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (30, 30, 30), 2, cv2.LINE_AA)
    
    # Tanggal, Waktu & Nama Efek
    date_str = time.strftime("%d %b %Y | %H:%M WIB")
    info_str = f"{date_str} - [{effect_name}]"
    cv2.putText(framed, info_str, (left + 10, h - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
                
    return framed


# ==========================================
# INISIALISASI KAMERA & DETEKTOR TANGAN
# ==========================================
print("Membuka kamera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

hand_detector = HandDetector(detectionCon=0.8, maxHands=2)

timer_start = None
photo_cooldown_end = 0
COUNTDOWN_TIME = 3.0
COOLDOWN_TIME = 5.0

print("Program Siap! Tekan 'ESC' for exit.")

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    effect_img = img.copy()

    hands, _ = hand_detector.findHands(img.copy(), draw=False)

    current_time = time.time()
    is_frame_pose = False
    active_effect_name = "NORMAL"

    # 1. DETEKSI POSE BINGKAI 2 TANGAN
    if len(hands) == 2:
        f1 = hand_detector.fingersUp(hands[0])
        f2 = hand_detector.fingersUp(hands[1])

        h1_is_l = (f1[1] == 1 and f1[2] == 0 and f1[3] == 0 and f1[4] == 0)
        h2_is_l = (f2[1] == 1 and f2[2] == 0 and f2[3] == 0 and f2[4] == 0)

        if h1_is_l and h2_is_l:
            is_frame_pose = True

    # 2. DETEKSI EFEK PADA JARI
    if hands:
        hand = hands[0]
        fingers = hand_detector.fingersUp(hand)

        is_two_fingers = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0)
        is_three_fingers = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0)
        is_five_fingers = (sum(fingers) == 5)

        if is_five_fingers:
            effect_img = cv2.GaussianBlur(effect_img, (51, 51), 0)
            active_effect_name = "BLUR"
        elif is_three_fingers:
            effect_img = cv2.convertScaleAbs(effect_img, alpha=1.2, beta=-10)
            h, w, _ = effect_img.shape
            bar_height = int(h * 0.12)
            effect_img[0:bar_height, :] = 0
            effect_img[h-bar_height:h, :] = 0
            active_effect_name = ""
        elif is_two_fingers:
            effect_img = cv2.convertScaleAbs(effect_img, alpha=0.3, beta=0)
            active_effect_name = "GELAP"

    display_img = effect_img.copy()

    # 3. LOGIKA COUNTDOWN & CETAK PHOTOBOOTH
    if current_time < photo_cooldown_end:
        sisa_jeda = int(photo_cooldown_end - current_time) + 1
        cv2.putText(display_img, f'JEDA FOTO: {sisa_jeda}s', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        timer_start = None

    else:
        if is_frame_pose and timer_start is None:
            timer_start = current_time

        if timer_start is not None:
            elapsed = current_time - timer_start
            sisa_timer = int(COUNTDOWN_TIME - elapsed) + 1

            if elapsed < COUNTDOWN_TIME:
                cv2.putText(display_img, f'FOTO: {sisa_timer}', (220, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
                cv2.putText(display_img, f'EFEK: {active_effect_name}', (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            else:
                # PASANG BINGKAI PHOTOBOOTH DAN SIMPAN
                photobooth_photo = apply_photobooth_frame(effect_img, active_effect_name)
                filename = f"photobooth_{active_effect_name}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, photobooth_photo)
                print(f"[BERHASIL] Foto Photobooth tersimpan: {filename}")

                # Flash Layar
                display_img[:] = 255
                cv2.putText(display_img, "PHOTOBOOTH SAVED!", (120, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                photo_cooldown_end = time.time() + COOLDOWN_TIME
                timer_start = None

        else:
            cv2.putText(display_img, f'EFEK: {active_effect_name}', (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Deteksi Jari (Rubu AI)", display_img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()