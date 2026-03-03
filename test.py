import time
import threading
import sys
import os
import random
from neonize.client import NewClient
from neonize.events import ConnectedEv, event
from neonize.utils import build_jid

# 1. Daftar Pertanyaan (Silahkan tambah sesuka hati)
PERTANYAAN = [
    "Halooo",
    "Apa saja paket yang ada",
    "Aku lagi butuh saran dong",
    "Aku mau cek jadwal bree"
]

def run_bot(session_name, acc_id, target_jid, total_msg, stop_event, start_barrier, num_acc):
    client = NewClient(session_name)

    @client.event(ConnectedEv)
    def on_connected(client: NewClient, __):
        print(f"✅ Akun {acc_id}: Connected!")
        
        # --- LOGIKA SINKRONISASI BARRIER ---
        if num_acc > 1:
            print(f"🚦 Akun {acc_id}: Menunggu akun lain...")
            try:
                start_barrier.wait(timeout=60)
            except threading.BrokenBarrierError:
                pass
        
        # --- PROSES PENGIRIMAN DENGAN WARM-UP ---
        for i in range(total_msg):
            msg_content = PERTANYAAN[i % len(PERTANYAAN)]
            try:
                # 1. TAHAP WARM-UP (Pesan 1-3)
                # Memberikan waktu bagi Signal Protocol untuk sinkronisasi kunci
                if i < 3:
                    # Jeda acak sedikit agar tidak benar-benar tabrakan di detik ke-0
                    time.sleep(random.uniform(0.5, 1.1)) 
                else:
                    # 2. TAHAP STRESS TEST (Pesan 4 keatas)
                    # Kecepatan penuh setelah sesi dianggap stabil
                    time.sleep(1.0 if num_acc == 1 else 0.5)

                client.send_message(target_jid, f"[STRESS-TEST-{acc_id}] {msg_content} (Ke-{i+1})")
                print(f"🚀 [Akun {acc_id}] Tembak pesan ke-{i+1}...")

            except Exception as e:
                print(f"❌ [Akun {acc_id}] Error: {e}")
                # Jika error MAC, istirahat sejenak lalu coba lagi
                time.sleep(5)
                continue
        
        print(f"🏁 Akun {acc_id}: Selesai.")
        time.sleep(5)
        client.disconnect()
        stop_event.set()

    print(f"🔗 Akun {acc_id}: Menghubungkan...")
    client.connect()

def main():
    print("\n" + "="*45)
    print(" 🤖 NEONIZE STRESS TESTER - FINAL VERSION ")
    print("="*45)
    
    pilihan = input("\n[1] Single\n[2] Multi\nPilih: ") or "1"
    num_acc = 1 if pilihan == "1" else int(input("Jumlah akun: ") or 2)

    target_num = input("Nomor tujuan: ") or "6281297542934"
    jid = build_jid(target_num)
    total_msg_per_acc = int(input("Pesan per akun: ") or 10)

    start_barrier = threading.Barrier(num_acc)
    stop_events = []

    print(f"\n🚀 Memulai {num_acc} session...")

    for i in range(num_acc):
        acc_id = i + 1
        session_name = f"session_acc_{acc_id}.sqlite3"
        stop_event = threading.Event()
        stop_events.append(stop_event)
        
        t = threading.Thread(
            target=run_bot, 
            args=(session_name, acc_id, jid, total_msg_per_acc, stop_event, start_barrier, num_acc)
        )
        t.daemon = True
        t.start()
        time.sleep(1) # Jeda antar thread login agar database tidak lock

    # Menunggu semua selesai
    try:
        for e in stop_events:
            e.wait()
    except KeyboardInterrupt:
        pass

    print("\n✨ Stress Test Selesai.")
    os._exit(0)

if __name__ == "__main__":
    main()
