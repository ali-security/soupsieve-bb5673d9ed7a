"""Test attribute selectors."""
import signal
import time
from .. import util
import soupsieve as sv


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_long_quoted_value(self):
        """Test that a long, well formed quoted value still parses and matches."""

        value = 'x' * 300
        markup = '<div id="0" data-attr="{}"></div>\n<div id="1" data-attr="y"></div>'.format(value)

        self.assert_selector(markup, '[data-attr="{}"]'.format(value), ["0"], flags=util.PYHTML)
        self.assert_selector(markup, "[data-attr='{}']".format(value), ["0"], flags=util.PYHTML)

    def test_pseudo_class_long_quoted_value(self):
        """Test that a long, well formed quoted value still parses in a pseudo-class."""

        value = 'x' * 300
        markup = '<div id="0">{}</div>\n<div id="1">y</div>'.format(value)

        self.assert_selector(markup, 'div:-soup-contains("{}")'.format(value), ["0"], flags=util.PYHTML)
        self.assert_selector(markup, "div:-soup-contains('{}')".format(value), ["0"], flags=util.PYHTML)

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        def timeout_handler(signum, frame):
            """Abort the parse once the alarm fires."""

            raise TimeoutError

        value = 'x' * 300
        # Every place a quoted value is accepted: a quote that is never closed must
        # fail fast with a syntax error instead of driving the parser into
        # catastrophic backtracking.
        prefixes = ('[a="', "[a='", ':-soup-contains("', ":-soup-contains('", ':lang("', ":lang('")

        # `SIGALRM` is absent on Windows, so bound the parse with an alarm where the
        # platform has one and fall back to measuring elapsed time everywhere else.
        alarm = hasattr(signal, 'SIGALRM')
        original = signal.signal(signal.SIGALRM, timeout_handler) if alarm else None
        try:
            for prefix in prefixes:
                if alarm:
                    signal.alarm(3)
                try:
                    start = time.perf_counter()
                    with self.assertRaises(sv.SelectorSyntaxError):
                        sv.compile(prefix + value)
                    elapsed = time.perf_counter() - start
                except TimeoutError:
                    self.fail('Timed out parsing {!r}'.format(prefix))
                finally:
                    if alarm:
                        signal.alarm(0)
                self.assertLess(elapsed, 10, 'Slow parse of {!r}: {}s'.format(prefix, elapsed))
        finally:
            if alarm:
                signal.signal(signal.SIGALRM, original)
