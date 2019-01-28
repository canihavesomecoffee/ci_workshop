from unittest import TestCase

from hint import WorkshopHints, GITHUB, TextHint, ScreenshotHint, CodeHint, Hint


class TestHint(TestCase):
    def test_that_a_hint_can_be_a_text_hint(self):
        expected = "Foo bar"
        h = TextHint(1, expected)
        self.assertEqual(h.text, expected)

    def test_that_a_hint_can_be_a_screenshot_hint(self):
        expected_img = "foo.png"
        expected_alt = "bar"
        expected_caption = "baz"
        h = ScreenshotHint(1, expected_img, expected_alt, expected_caption)
        self.assertEqual(h.image, expected_img)
        self.assertEqual(h.alt, expected_alt)
        self.assertEqual(h.caption, expected_caption)

    def test_that_a_hint_can_be_a_screenshot_hint_with_no_caption(self):
        expected_img = "foo.png"
        expected_alt = "bar"
        expected_caption = ""
        h = ScreenshotHint(1, expected_img, expected_alt)
        self.assertEqual(h.image, expected_img)
        self.assertEqual(h.alt, expected_alt)
        self.assertEqual(h.caption, expected_caption)

    def test_that_a_hint_can_be_a_code_hint(self):
        expected_code = ["foo", "bar", "baz"]
        h = CodeHint(1, expected_code)
        self.assertEqual(h.code, expected_code)

    def test_that_the_hint_base_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Hint(1)


class TestWorkshopHints(TestCase):
    def test_that_getting_hints_for_an_unknown_step_returns_an_empty_list(self):
        h = WorkshopHints()
        self.assertEqual(0, len(h.get_hints_for_step(1337)))

    def test_that_getting_hints_for_an_known_step_returns_an_empty_list(self):
        h = WorkshopHints()
        self.assertNotEqual(0, len(h.get_hints_for_step(GITHUB)))
