import unittest
import xml_jstatutree as jstatutree

class JSTTreeTestCase(unittest.TestCase):
    def setUp(self):
        self.widget = Widget('The widget')

    def tearDown(self):
        self.widget.dispose()