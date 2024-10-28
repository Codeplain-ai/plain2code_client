#!/usr/bin/env python3

import unittest
import subprocess

class TestHelloWorld(unittest.TestCase):
    def test_hello_world_output(self):
        # Run the hello_world.py script and capture its output
        result = subprocess.run(['python3', 'hello_world.py'], capture_output=True, text=True)
        
        # Check if the output matches the expected string
        self.assertEqual(result.stdout.strip(), "hello, world")

if __name__ == '__main__':
    unittest.main()