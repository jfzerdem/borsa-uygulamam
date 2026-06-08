from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import ta

app = Flask(__name__)
CORS(app) # Telefonunun bilgisayardaki bu koda bağlanabilmesi için izin

@app.route('/api/analiz', methods=['GET'])
def analiz_et():
    hisse = request.args.get('hisse', '').upper()
    if not hisse:
        return jsonify({"hata": "Hisse kodu eksik"}), 400
        
    try:
        # Verileri Yahoo Finance üzerinden BIST formatında çekiyoruz (.IS)
        ticker = f"{hisse}.IS"
        data = yf.download(ticker, period="6mo", interval="1d")
        
        if data.empty or len(data) < 20:
            return jsonify({"hata": "Hisse bulunamadı veya veri yetersiz."}), 404
            
        guncel_fiyat = float(data['Close'].iloc[-1])
        
        # 1. RSI Hesaplama
        rsi_serisi = ta.momentum.rsi(data['Close'], window=14)
        guncel_rsi = float(rsi_serisi.iloc[-1])
        
        # 2. MACD Hesaplama
        macd_obj = ta.trend.MACD(data['Close'])
        macd_diff = float(macd_obj.macd_diff().iloc[-1])
        macd_durum = "Yükseliş Eğilimi (AL)" if macd_diff > 0 else "Düşüş Eğilimi (SAT)"
        
        # 3. Basit Destek/Direnç (Son 1 ayın en düşük/en yükseği)
        destek = float(data['Low'].tail(30).min())
        direnc = float(data['High'].tail(30).max())
        
        # 4. Al-Sat Sinyal Algoritması
        if guncel_rsi < 35 and macd_diff > 0:
            strateji = "🤖 AI: GÜÇLÜ ALIM BÖLGESİ"
        elif guncel_rsi > 70 and macd_diff < 0:
            strateji = "🤖 AI: GÜÇLÜ SATIM BÖLGESİ"
        elif guncel_rsi < 45:
            strateji = "🤖 AI: KADEMELİ ALIMA UYGUN"
        elif guncel_rsi > 65:
            strateji = "🤖 AI: KAR AL / SATIM UYGUN"
        else:
            strateji = "🤖 AI: BEKLE / NÖTR KONUM"

        return jsonify({
            "Hisse": hisse,
            "Fiyat": round(guncel_fiyat, 2),
            "RSI": round(guncel_rsi, 2),
            "MACD": macd_durum,
            "Destek": round(destek, 2),
            "Direnç": round(direnc, 2),
            "Strateji": strateji
        })
        
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

if __name__ == '__main__':
    # Dışarıdan (telefondan) erişim için host='0.0.0.0' yapıyoruz
    app.run(host='0.0.0.0', port=5000, debug=True)