from sqlalchemy.sql.expression import select
from models import CardFaq, Card, Faq, HistoryCard, HistoryFaq

from models.dependencies import async_session


async def save_card(
    card_id,
    card_name,
    card_text,
    card_supplement,
    card_supplement_date,
    p_effect,
    p_supplement,
    p_supplement_date,
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
    async with async_session() as session:
        async with session.begin():
            cards = await session.execute(select(Card).where(Card.card_id == card_id))
            card = cards.scalar()
            if card is None:
                session.add(
                    Card(
                        card_id=card_id,
                        name=card_name,
                        text=card_text,
                        supplement=card_supplement,
                        supplement_date=card_supplement_date,
                        p_effect=p_effect,
                        p_supplement=p_supplement,
                        p_supplement_date=p_supplement_date,
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
            elif (
                card.text,
                card.supplement,
                card.supplement_date,
                card.p_effect,
                card.p_supplement,
                card.p_supplement_date,
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
                card_text,
                card_supplement,
                card_supplement_date,
                p_effect,
                p_supplement,
                p_supplement_date,
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
                card.text = card_text
                card.supplement = card_supplement
                card.supplement_date = card_supplement_date
                card.p_effect = p_effect
                card.p_supplement = p_supplement
                card.p_supplement_date = p_supplement_date
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


async def save_faq(cards_id, faq_id, title, question, answer, tags, date):
    async with async_session() as session:
        async with session.begin():
            faqs = await session.execute(select(Faq).where(Faq.faq_id == faq_id))
            faq = faqs.scalar()
            if faq is None:
                session.add(
                    Faq(
                        faq_id=faq_id,
                        title=title,
                        question=question,
                        answer=answer,
                        tags=' '.join(tags),
                        date=date,
                    )
                )
                for card_id in cards_id:
                    session.add(CardFaq(card_id=card_id, faq_id=faq_id))
            elif (faq.title, faq.question, faq.answer, faq.tags, faq.date) != (
                title,
                question,
                answer,
                ' '.join(tags),
                date,
            ):
                session.add(
                    HistoryFaq(
                        faq_id=faq.faq_id,
                        title=faq.title,
                        question=faq.question,
                        answer=faq.answer,
                        tags=faq.tags,
                        date=faq.date,
                    )
                )
                faq.faq_id = faq_id
                faq.title = title
                faq.question = question
                faq.answer = answer
                faq.tags = tags
                faq.date = date

                old_cards_faq = await session.execute(select(CardFaq).where(CardFaq.faq_id==faq_id))
                old_cards_id = set()
                for old_card_faq in old_cards_faq.scalars():
                    if old_card_faq.card_id not in cards_id:
                        old_card_faq.delete_flag = 1
                    old_cards_id.add(old_card_faq.card_id)
                for card_id in cards_id - old_cards_id:
                    session.add(CardFaq(card_id=card_id, faq_id=faq_id))


async def delete_faq(faq_id):
    async with async_session() as session:
        async with session.begin():
            faqs = await session.execute(select(Faq).where(faq_id == faq_id))
            faq = faqs.scalar()
            if faq is None:
                return
            faq.delete_flag = 1
            card_faqs = await session.execute(select(CardFaq).where(faq_id == faq_id))
            for card_faq in card_faqs.scalars():
                card_faq.delete_flag = 1
