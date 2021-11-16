import json
import io

alle = []
with open("-f copy.txt", encoding='utf-8') as f:
    alle = f.readlines()
out = io.open('-f_new.txt', 'w', encoding="utf-8")
for line in alle:
    in_as_obj = json.loads(line)
    json.dump(in_as_obj, out, ensure_ascii=False)
    out.write('\n')
out.close()