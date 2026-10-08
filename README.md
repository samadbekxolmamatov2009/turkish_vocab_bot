# turkish_vocab_bot

Turkcha so'zlar uchun Telegram test boti (A1, A2, B1, B2, C1).

- User daraja tanlaydi → tanlangan darajadan tasodifiy turkcha so'z chiqadi, 3 ta o'zbekcha variantdan birini tanlaydi.
- Admin so'zlarni bot ichidagi admin panel orqali qo'shadi.

## Ishga tushirish
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN va ADMIN_IDS ni to'ldiring
python main.py
```

## Buyruqlar
User: `/start`, `/stats`
Admin: `/admin`, `/add`, `/list`, `/del ID`

So'z qo'shish formati (har qatorda bittadan): `merhaba - salom`
Har bir darajada test ishlashi uchun kamida 3 ta so'z kerak.
