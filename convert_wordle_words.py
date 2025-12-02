#!/usr/bin/env python3
"""
Convert wordle-words-unedited.txt to CSV format for import.

Input format:  "    Day 0, Jun 19 2021: CIGAR"
Output format: "#0,CIGAR"
"""
import re

# Pattern: "Day 123, Mon DD YYYY: WORD"
pattern = r'Day\s+(\d+),.*:\s+(\w+)'

with open('wordle-words-unedited.txt', 'r') as infile:
    with open('wordle-words-complete.csv', 'w') as outfile:
        for line in infile:
            match = re.search(pattern, line)
            if match:
                day_num = match.group(1)
                word = match.group(2).upper()
                outfile.write(f'#{day_num},{word}\n')

print("Conversion complete! Output written to wordle-words-complete.csv")
