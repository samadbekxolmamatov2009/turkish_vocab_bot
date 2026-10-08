import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import db
from .config import LEVELS

router = Router()


def levels_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=l, callback_data=f"lvl:{l}") for l in LEVELS[:3]],
            [InlineKeyboardButton(text=l, callback_data=f"lvl:{l}") for l in LEVELS[3:]]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_question(target: Message, level: str) -> None:
    q = await db.random_question(level)
    if not q:
        await target.answer(
            f"{level} darajasida hozircha yetarli so'z yo'q (kamida 3 ta kerak). "
            "Boshqa daraja tanlang: /start"
        )
        return
    word, wrong = q
    options = [(word[0], word[2])] + [(i, uz) for i, uz in wrong]
    random.shuffle(options)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz, callback_data=f"ans:{level}:{word[0]}:{oid}")]
        for oid, uz in options
    ])
    await target.answer(f"📚 {level}\n\n<b>{word[1]}</b> — qanday tarjima qilinadi?",
                        reply_markup=kb, parse_mode="HTML")


@router.message(Command("start"))
async def start(m: Message) -> None:
    await m.answer("Salom! Turkcha so'zlar testi. Darajani tanlang:", reply_markup=levels_kb())


@router.message(Command("stats"))
async def stats(m: Message) -> None:
    c, w = await db.get_stats(m.from_user.id)
    total = c + w
    pct = round(c * 100 / total) if total else 0
    await m.answer(f"📊 To'g'ri: {c}\nXato: {w}\nNatija: {pct}%")


@router.callback_query(F.data.startswith("lvl:"))
async def choose_level(cb: CallbackQuery) -> None:
    await cb.answer()
    await send_question(cb.message, cb.data.split(":")[1])


@router.callback_query(F.data.startswith("ans:"))
async def answer(cb: CallbackQuery) -> None:
    _, level, word_id, chosen_id = cb.data.split(":")
    word = await db.get_word(int(word_id))
    if not word:
        await cb.answer("So'z topilmadi", show_alert=True)
        return
    ok = word_id == chosen_id
    c, w = await db.record_answer(cb.from_user.id, ok)
    verdict = "✅ To'g'ri!" if ok else f"❌ Xato. To'g'ri javob: <b>{word[3]}</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"lvl:{level}"),
         InlineKeyboardButton(text="🔄 Daraja", callback_data="menu")]
    ])
    await cb.message.edit_text(
        f"<b>{word[2]}</b> = {word[3]}\n\n{verdict}\n\n✔️ {c}  ✖️ {w}",
        reply_markup=kb, parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery) -> None:
    await cb.message.answer("Darajani tanlang:", reply_markup=levels_kb())
    await cb.answer()
