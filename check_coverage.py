#!/usr/bin/env python
import xml.etree.ElementTree as ET

tree = ET.parse("coverage.xml")
root = tree.getroot()

# Get overall stats
sources = root.findall(".//sources/source")
packages = root.findall(".//package")

incomplete = []
complete = []

for pkg in packages:
    for cls in pkg.findall(".//class"):
        fname = cls.get("filename", "")
        line_rate = float(cls.get("line-rate", "0"))

        if line_rate < 1.0:
            incomplete.append((fname, line_rate))
        else:
            complete.append(fname)

incomplete.sort(key=lambda x: x[1])

print(f"Total files with <100% coverage: {len(incomplete)}")
print(f"Total files with 100% coverage: {len(complete)}")
print("\nIncomplete files:")
for fname, rate in incomplete[:30]:
    pct = rate * 100
    print(f"  {fname}: {pct:.1f}%")
