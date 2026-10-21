import xml.etree.ElementTree as ET
from xml.dom import minidom

STATES = [
    (0, "q0", 100, 300, True, False),
    # Идентификаторы
    (1, "q1_id", 300, 80, False, False),
    (2, "q2_id*", 520, 80, False, True),
    # Числа
    (4, "q4_int", 280, 200, False, False),
    (5, "q5_int*", 480, 160, False, True),
    (6, "q6_frac", 450, 240, False, False),
    (7, "q7_dot", 260, 270, False, False),
    (8, "q8_flt*", 620, 220, False, True),
    (9, "q9_exp", 580, 280, False, False),
    (10, "q10_sgn", 700, 280, False, False),
    (11, "q11_expd", 820, 280, False, False),
    (13, "q13_exp*", 960, 280, False, True),
    # Строки
    (14, "q14_str", 300, 360, False, False),
    (15, "q15_esc", 450, 360, False, False),
    (16, "q16_str", 600, 360, False, True),
    # Разделители / односимвольные
    (18, "q18_op*", 520, 480, False, True),
    (19, "q19_nl", 300, 430, False, True),
    (20, "q20_cmt", 300, 500, False, False),
    # Составные операторы
    (21, "q21_lt", 280, 560, False, False),
    (22, "q22_assign", 480, 540, False, True),
    (23, "q23_le", 480, 580, False, True),
    (24, "q24_gt", 280, 640, False, False),
    (25, "q25_ge", 480, 640, False, True),
    (26, "q26_eq", 280, 710, False, False),
    (27, "q27_eqeq", 480, 710, False, True),
    (28, "q28_not", 280, 780, False, False),
    (29, "q29_ne", 480, 780, False, True),
    (30, "q30_punct", 280, 850, False, True),
    # Ошибки
    (101, "q101_ERR", 100, 600, False, True),
    (102, "q102_ERR", 700, 200, False, True),
    (103, "q103_ERR", 450, 430, False, True),
]

TRANSITIONS = [
    (0, 0, "ws"),
    (0, 19, "nl"),
    (0, 20, "#"),
    (20, 20, "other"),
    (20, 19, "nl"),
    (0, 1, "Letter"),
    (1, 1, "Letter"),
    (1, 1, "Digit"),
    (1, 2, "other"),
    (0, 4, "Digit"),
    (4, 4, "Digit"),
    (4, 5, "other"),
    (4, 6, "dot"),
    (4, 9, "exp"),
    (0, 7, "dot"),
    (7, 6, "Digit"),
    (7, 101, "other"),
    (6, 6, "Digit"),
    (6, 8, "other"),
    (6, 9, "exp"),
    (9, 10, "sign"),
    (9, 11, "Digit"),
    (9, 102, "other"),
    (10, 11, "Digit"),
    (10, 102, "other"),
    (11, 11, "Digit"),
    (11, 13, "other"),
    (0, 14, "quote"),
    (14, 14, "other"),
    (14, 15, "escape"),
    (14, 16, "quote"),
    (14, 103, "nl"),
    (15, 14, "escaped_ch"),
    (15, 103, "other"),
    (0, 21, "<"),
    (21, 22, "-"),
    (21, 23, "="),
    (21, 18, "other"),
    (0, 24, ">"),
    (24, 25, "="),
    (24, 18, "other"),
    (0, 26, "="),
    (26, 27, "="),
    (26, 101, "other"),
    (0, 28, "!"),
    (28, 29, "="),
    (28, 18, "other"),
    (0, 30, "; , ( ) { } [ ] + - * / ^ & |"),
    (0, 101, "other"),
]


def generate_jff(filename="rlite_automaton.jff"):
    structure = ET.Element("structure")
    type_elem = ET.SubElement(structure, "type")
    type_elem.text = "fa"

    automaton = ET.SubElement(structure, "automaton")
    automaton.append(ET.Comment("The list of states."))

    for state_id, name, x, y, is_init, is_final in STATES:
        s = ET.SubElement(automaton, "state", id=str(state_id), name=name)
        x_elem = ET.SubElement(s, "x")
        x_elem.text = f"{x:.1f}"
        y_elem = ET.SubElement(s, "y")
        y_elem.text = f"{y:.1f}"
        if is_init:
            ET.SubElement(s, "initial")
        if is_final:
            ET.SubElement(s, "final")

    automaton.append(ET.Comment("The list of transitions."))
    for from_id, to_id, label in TRANSITIONS:
        t = ET.SubElement(automaton, "transition")
        f_elem = ET.SubElement(t, "from")
        f_elem.text = str(from_id)
        to_elem = ET.SubElement(t, "to")
        to_elem.text = str(to_id)
        r_elem = ET.SubElement(t, "read")
        r_elem.text = label

    xml_str = ET.tostring(structure, encoding="utf-8")
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="  ", encoding="UTF-8")

    with open(filename, "wb") as f:
        f.write(pretty_xml)
    print(f"Файл {filename} успішно згенеровано!")


if __name__ == "__main__":
    generate_jff()