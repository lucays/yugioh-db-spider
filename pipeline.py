from sqlalchemy.sql.expression import select, update

from models import (
    CardFaq,
    Card,
    Faq,
    Supplement,
    HistoryCard,
    HistoryFaq,
    HistorySupplement,
)
from models.dependencies import async_session
from configs.log_config import logger


async def save_or_update_faq(datas: list):
    async with async_session() as session:
        async with session.begin():
            for cards_id, faq_id, title, question, answer, tags, date in datas:
                if tags and tags[0].strip() == "最新Ｑ＆Ａ":
                    tags = tags[1:]
                faqs = await session.execute(select(Faq).where(Faq.faq_id == faq_id))
                faq = faqs.scalar()
                if faq is None:
                    session.add(
                        Faq(
                            faq_id=faq_id,
                            title=title,
                            question=question,
                            answer=answer,
                            tags=" ".join(tags),
                            date=date,
                        )
                    )
                    for card_id in cards_id:
                        session.add(CardFaq(card_id=card_id, faq_id=faq_id))
                    logger.info(f"faq id: {faq_id}, title: {title}, cards id: {cards_id} saved")
                elif (faq.title, faq.question, faq.answer, faq.tags, faq.date) != (
                    title,
                    question,
                    answer,
                    " ".join(tags),
                    date,
                ):
                    session.add(
                        HistoryFaq(
                            faq_id=faq.faq_id,
                            title=faq.title,
                            question=faq.question,
                            answer=faq.answer,
                            tags=" ".join(tags),
                            date=faq.date,
                        )
                    )
                    faq.faq_id = faq_id
                    faq.title = title
                    faq.question = question
                    faq.answer = answer
                    faq.tags = tags
                    faq.date = date

                    old_cards_faq = await session.execute(select(CardFaq).where(CardFaq.faq_id == faq_id))
                    old_cards_id = set()
                    for old_card_faq in old_cards_faq.scalars():
                        if old_card_faq.card_id not in cards_id:
                            old_card_faq.delete_flag = 1
                        old_cards_id.add(old_card_faq.card_id)
                    for card_id in cards_id - old_cards_id:
                        session.add(CardFaq(card_id=card_id, faq_id=faq_id))
                    logger.info(f"faq id: {faq_id}, title: {title}, cards id: {cards_id} updated")


async def delete_faq(faqs_id):
    async with async_session() as session:
        async with session.begin():
            await session.execute(update(Faq).where(Faq.faq_id.in_(faqs_id)).values(delete_flag=1))
            await session.execute(update(CardFaq).where(CardFaq.faq_id.in_(faqs_id)).values(delete_flag=1))


async def card_exist(cards_id: list):
    exist_cards_id = []
    async with async_session() as session:
        async with session.begin():
            query = await session.execute(select(Card).where(Card.card_id.in_(cards_id)))
            for card in query.scalars():
                exist_cards_id.append(card.card_id)
    return set(cards_id) - set(exist_cards_id)


async def get_faqs_id_date(card_id: int):
    async with async_session() as session:
        async with session.begin():
            query = await session.execute(select(CardFaq).where(CardFaq.card_id == card_id))
            faqs_id = [card_faq.faq_id for card_faq in query.scalars() if not card_faq.delete_flag]
            query = await session.execute(select(Faq).where(Faq.id.in_(faqs_id)))
            faqs_id_date = {(faq.id, faq.date) for faq in query.scalars() if not faq.delete_flag}
    return faqs_id_date


async def save_or_update_card(datas):
    async with async_session() as session:
        async with session.begin():
            for card_id, card_name, type_, attr, level, rank, link_rating, p_scale, attack, defense, src_url, monster_types in datas:
                cards = await session.execute(select(Card).where(Card.card_id == card_id))
                card = cards.scalar()
                if card is None:
                    session.add(
                        Card(
                            card_id=card_id,
                            name=card_name,
                            type_=type_,
                            attr=attr,
                            level=level,
                            rank=rank,
                            link_rating=link_rating,
                            p_scale=p_scale,
                            attack=attack,
                            defense=defense,
                            src_url=src_url,
                            monster_types=monster_types,
                        )
                    )
                    logger.info(f"card id: {card_id}, card_name: {card_name} saved")
                elif (
                    card.type_,
                    card.attr,
                    card.level,
                    card.rank,
                    card.link_rating,
                    card.p_scale,
                    card.attack,
                    card.defense,
                    card.src_url,
                    card.monster_types,
                ) != (
                    type_,
                    attr,
                    level,
                    rank,
                    link_rating,
                    p_scale,
                    attack,
                    defense,
                    src_url,
                    monster_types,
                ):
                    # history add card
                    # update new card info
                    session.add(
                        HistoryCard(
                            card_id=card.card_id,
                            name=card.name,
                            text=card.text,
                            supplement=card.supplement,
                            supplement_date=card.supplement_date,
                            p_effect=card.p_effect,
                            p_supplement=card.p_supplement,
                            p_supplement_date=card.p_supplement_date,
                            type_=type_,
                            attr=card.attr,
                            level=card.level,
                            rank=card.rank,
                            link_rating=card.link_rating,
                            p_scale=card.p_scale,
                            attack=card.attack,
                            defense=card.defense,
                            src_url=card.src_url,
                            monster_types=card.monster_types,
                        )
                    )
                    card.name = card_name
                    card.type_ = type_
                    card.attr = attr
                    card.level = level
                    card.rank = rank
                    card.link_rating = link_rating
                    card.p_scale = p_scale
                    card.attack = attack
                    card.defense = defense
                    card.src_url = src_url
                    card.monster_types = monster_types
                    logger.info(f"card id: {card_id}, card_name: {card_name} updated")


async def save_or_update_supplement(datas):
    results = {}
    async with async_session() as session:
        async with session.begin():
            for card_id, card_name, card_effect, card_supplement, card_supplement_date, p_effect, p_supplement, p_supplement_date in datas:
                saved, updated = False, False
                cards = await session.execute(select(Supplement).where(Supplement.card_id == card_id))
                card = cards.scalar()
                if card is None:
                    session.add(
                        Supplement(
                            card_id=card_id,
                            name=card_name,
                            effect=card_effect,
                            supplement=card_supplement,
                            supplement_date=card_supplement_date,
                            p_effect=p_effect,
                            p_supplement=p_supplement,
                            p_supplement_date=p_supplement_date,
                        )
                    )
                    saved = True
                    logger.info(f"card id: {card_id}, card_name: {card_name} supplement saved")
                elif (card.effect, card.supplement, card.supplement_date, card.p_effect, card.p_supplement, card.p_supplement_date,) != (
                    card_effect,
                    card_supplement,
                    card_supplement_date,
                    p_effect,
                    p_supplement,
                    p_supplement_date,
                ):
                    # history add card
                    # update new card info
                    session.add(
                        HistorySupplement(
                            card_id=card.card_id,
                            name=card.name,
                            effect=card.effect,
                            supplement=card.supplement,
                            supplement_date=card.supplement_date,
                            p_effect=card.p_effect,
                            p_supplement=card.p_supplement,
                            p_supplement_date=card.p_supplement_date,
                        )
                    )
                    card.name = card_name
                    card.effect = card_effect
                    card.supplement = card_supplement
                    card.supplement_date = card_supplement_date
                    card.p_effect = p_effect
                    card.p_supplement = p_supplement
                    card.p_supplement_date = p_supplement_date
                    updated = True
                    logger.info(f"card id: {card_id}, card_name: {card_name} supplement updated")
                results[card_id] = (saved, updated)
    return results
