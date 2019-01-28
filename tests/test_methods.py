from random import randint

from ci_demo import get_valid_step, User, retrieve_next_hint, get_active_hints, UserHints, db, unlock_all_hints_for_step
from hint import WorkshopHints, TextHint
from tests.base import BaseTestCase


class TestMethods(BaseTestCase):
    def test_get_valid_step_returns_one_if_the_step_is_zero_or_less(self):
        self.assertEqual(1, get_valid_step(0, 5))
        self.assertEqual(1, get_valid_step(randint(-2000, -1), 5))

    def test_get_valid_step_returns_the_maximum_if_the_step_is_more_than_the_maximum(self):
        expected = 5
        self.assertEqual(expected, get_valid_step(6, expected))
        self.assertEqual(expected, get_valid_step(randint(expected + 1, 3000), expected))

    def test_get_valid_step_returns_the_step_if_the_step_is_within_bounds(self):
        expected = 5
        self.assertEqual(expected, get_valid_step(expected, expected))
        self.assertEqual(expected, get_valid_step(expected, expected + 1))

    def test_get_active_hints_returns_no_active_hints_if_there_were_none_activated_yet(self):
        non_activated_hint = TextHint(1, "foo")
        hints_with_non_activated_hint = WorkshopHints({3: [non_activated_hint]})
        u = User(workshop_step=3)
        self.assertListEqual([], get_active_hints(u, hints_with_non_activated_hint))

    def test_get_active_hints_returns_no_active_hints_if_there_were_none_in_that_step(self):
        u = User(workshop_step=1)
        self.assertListEqual([], get_active_hints(u, WorkshopHints({})))

    def test_get_active_hints_returns_active_hints(self):
        u = User(workshop_step=2)
        u.hints = [UserHints(id=1), UserHints(id=2)]
        non_activated_hint = TextHint(1, "foo")
        activated_hint = TextHint(2, "foo")
        self.assertListEqual([activated_hint], get_active_hints(u, WorkshopHints({1: [non_activated_hint], 2: [activated_hint]})))

    def test_retrieve_next_hint_returns_nothing_if_no_hints_are_left(self):
        hints = WorkshopHints({1: []})
        user = User()
        self.assertEqual(None, retrieve_next_hint(user, 1, hints))

    def test_retrieve_next_hint_returns_the_first_hint(self):
        expected = TextHint(1, "foo")
        hints = WorkshopHints({1: [expected]})
        user = User()
        self.assertEqual(expected, retrieve_next_hint(user, 1, hints))

    def test_unlock_all_hints_for_step_unlocks_all_hints_for_the_user(self):
        u = self.create_user()
        hint = TextHint(1, "activated")
        user_hint = UserHints(id=hint.id, user_id=u.id)
        db.session.add(user_hint)
        db.session.commit()
        new_hint = TextHint(2, "not activated")
        self.assertIsNone(UserHints.query.filter(UserHints.id == new_hint.id).first())
        unlock_all_hints_for_step(1, u, WorkshopHints({1: [hint, new_hint]}))
        self.assertIsNotNone(UserHints.query.filter(UserHints.id == new_hint.id).first())
