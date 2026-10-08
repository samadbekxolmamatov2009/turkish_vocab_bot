from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import db
from .config import ADMIN_IDS, LEVELS

router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        return event.from_user.id in ADMIN_IDS


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddWords(StatesGroup):
    waiting = State()


def level_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l, callback_data=f"{prefix}:{l}") for l in LEVELS]
    ])


@router.message(Command("admin"))
async def admin(m: Message, state: FSMContext) -> None:
    await state.clear()
    counts = await db.count_by_level()
    stat = "\n".join(f"{l}: {counts.get(l, 0)} ta" for l in LEVELS)
    await m.answer(
        f"🛠 Admin panel\n\n{stat}\n\n"
        "/add — so'z qo'shish\n/list — so'zlar ro'yxati\n/del ID — so'zni o'chirish"
    )


@router.message(Command("add"))
async def add(m: Message) -> None:
    await m.answer("Qaysi darajaga qo'shamiz?", reply_markup=level_kb("addlvl"))


@router.callback_query(F.data.startswith("addlvl:"))
async def add_level(cb: CallbackQuery, state: FSMContext) -> None:
    level = cb.data.split(":")[1]
    await state.set_state(AddWords.waiting)
    await state.update_data(level=level)
    await cb.message.answer(
        f"{level} uchun so'zlarni yuboring, har qatorda bittadan:\n"
        "<code>turkcha - o'zbekcha</code>\n\nMasalan:\n<code>merhaba - salom\nkitap - kitob</code>\n\n"
        "Tugatish: /admin", parse_mode="HTML")
    await cb.answer()


@router.message(AddWords.waiting, ~F.text.startswith("/"))
async def add_words(m: Message, state: FSMContext) -> None:
    level = (await state.get_data())["level"]
    added = dup = 0
    bad = []
    for line in m.text.splitlines():
        if not line.strip():
            continue
        tr, sep, uz = line.partition(" - ")
        if not sep:
            tr, sep, uz = line.partition("-")
        tr, uz = tr.strip(), uz.strip()
        if not (sep and tr and uz):
            bad.append(line)
            continue
        if await db.add_word(level, tr, uz):
            added += 1
        else:
            dup += 1
    text = f"✅ Qo'shildi: {added}\n♻️ Takror: {dup}"
    if bad:
        text += "\n⚠️ Noto'g'ri format:\n" + "\n".join(bad)
    await m.answer(text + "\n\nYana yuboring yoki /admin")


@router.message(Command("list"))
async def list_cmd(m: Message) -> None:
    await m.answer("Qaysi daraja?", reply_markup=level_kb("listlvl"))


@router.callback_query(F.data.startswith("listlvl:"))
async def list_level(cb: CallbackQuery) -> None:
    level = cb.data.split(":")[1]
    rows = await db.list_words(level)
    body = "\n".join(f"{i}. {tr} — {uz}" for i, tr, uz in rows) or "Bo'sh"
    await cb.message.answer(f"{level} (oxirgi 50 ta):\n{body}\n\nO'chirish: /del ID")
    await cb.answer()


@router.message(Command("del"))
async def delete(m: Message) -> None:
    arg = m.text.partition(" ")[2].strip()
    if not arg.isdigit():
        await m.answer("Foydalanish: /del ID")
        return
    ok = await db.delete_word(int(arg))
    await m.answer("🗑 O'chirildi" if ok else "Topilmadi")
