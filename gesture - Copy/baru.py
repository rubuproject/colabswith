import cv2
import time
from cvzone.HandTrackingModule import HandDetector

# ==========================================
# INISIALISASI KAMERA & DETEKTOR TANGAN
# ==========================================
print("Membuka kamera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

hand_detector = HandDetector(detectionCon=0.8, maxHands=2)

# Variabel Kontrol
timer_start = None
photo_cooldown_end = 0
COUNTDOWN_TIME = 3.0   # Timer 3 detik
COOLDOWN_TIME = 5.0    # Jeda 5 detik

print("Program Siap! Tekan 'ESC' untuk keluar.")

while cap.isOpened():
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    
    # Salinan gambar bersih tempat efek akan diterapkan
    effect_img = img.copy()

    # Deteksi Tangan
    hands, _ = hand_detector.findHands(img.copy(), draw=False)

    current_time = time.time()
    is_frame_pose = False
    active_effect_name = ""

    # --- 1. CEK POSE BINGKAI (PEMICU TIMER) ---
    if len(hands) == 2:
        f1 = hand_detector.fingersUp(hands[0])
        f2 = hand_detector.fingersUp(hands[1])

        h1_is_l = (f1[1] == 1 and f1[2] == 0 and f1[3] == 0 and f1[4] == 0)
        h2_is_l = (f2[1] == 1 and f2[2] == 0 and f2[3] == 0 and f2[4] == 0)

        if h1_is_l and h2_is_l:
            is_frame_pose = True

    # --- 2. TERAPKAN EFEK VISUAL SESUAI GAYA JARI ---
    if hands:
        hand = hands[0]
        fingers = hand_detector.fingersUp(hand)

        is_two_fingers = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0)
        is_three_fingers = (fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0)
        is_five_fingers = (sum(fingers) == 5)

        # Efek Blur (5 Jari)
        if is_five_fingers:
            effect_img = cv2.GaussianBlur(effect_img, (51, 51), 0)
            active_effect_name = ""
            
        # Efek Cinematic (3 Jari)
        elif is_three_fingers:
            effect_img = cv2.convertScaleAbs(effect_img, alpha=1.2, beta=-10)
            h, w, _ = effect_img.shape
            bar_height = int(h * 0.12)
            effect_img[0:bar_height, :] = 0
            effect_img[h-bar_height:h, :] = 0
            active_effect_name = ""
            
        # Efek Gelap (2 Jari)
        elif is_two_fingers:
            effect_img = cv2.convertScaleAbs(effect_img, alpha=0.3, beta=0)
            active_effect_name = ""

    # Gambar yang ditampilkan ke layar monitor
    display_img = effect_img.copy()

    # --- 3. LOGIKA HITUNG MUNDUR & MEMFOTO ---
    
    # KONDISI A: Dalam jeda 5 detik setelah memfoto
    if current_time < photo_cooldown_end:
        sisa_jeda = int(photo_cooldown_end - current_time) + 1
        cv2.putText(display_img, f'JEDA FOTO: {sisa_jeda}s', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
        timer_start = None

    # KONDISI B: Timer sedang berjalan atau baru diaktifkan
    else:
        # Pemicu timer pertama kali saat pose bingkai terdeteksi
        if is_frame_pose and timer_start is None:
            timer_start = current_time

        # Jika timer sudah berjalan
        if timer_start is not None:
            elapsed = current_time - timer_start
            sisa_timer = int(COUNTDOWN_TIME - elapsed) + 1

            if elapsed < COUNTDOWN_TIME:
                # Tampilkan angka timer dan nama efek aktif
                cv2.putText(display_img, f'FOTO: {sisa_timer}', (220, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
                cv2.putText(display_img, f'EFEK: {active_effect_name}', (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            else:
                # WAKTU HABIS: Simpan gambar bersih BESERTA efek yang sedang aktif
                filename = f"foto_{active_effect_name}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, effect_img)
                print(f"[BERHASIL] Foto tersimpan: {filename}")

                # Flash Layar
                display_img[:] = 255
                cv2.putText(display_img, f"FOTO {active_effect_name} TERSIMPAN!", (80, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

                photo_cooldown_end = time.time() + COOLDOWN_TIME
                timer_start = None

        # KONDISI C: Tampilan normal
        else:
            cv2.putText(display_img, f'EFEK: {active_effect_name}', (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Deteksi Jari (Rubu AI)", display_img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()