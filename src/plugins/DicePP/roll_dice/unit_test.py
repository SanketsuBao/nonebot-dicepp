import unittest
import roll_config
from roll_dice.expression import parse_roll_exp, exec_roll_exp, RollExpression, preprocess_roll_exp
from roll_dice.roll_utils import match_outer_parentheses, remove_redundant_parentheses, RollDiceError
from roll_dice import RollResult


class MyTestCase(unittest.TestCase):
    def test_utils(self):
        self.assertEqual(match_outer_parentheses("()"), 1)
        self.assertEqual(match_outer_parentheses("(ABC)"), 4)
        self.assertEqual(match_outer_parentheses("(A()A)"), 5)
        self.assertEqual(match_outer_parentheses("(AA)))"), 3)
        self.assertEqual(match_outer_parentheses("()ABC"), 1)
        self.assertEqual(match_outer_parentheses("(1+2)+1"), 4)
        self.assertEqual(match_outer_parentheses("ABC"), -1)
        self.assertEqual(match_outer_parentheses(""), -1)
        self.assertEqual(match_outer_parentheses("ABC()"), -1)
        self.assertRaises(ValueError, match_outer_parentheses, "(((")
        self.assertRaises(ValueError, match_outer_parentheses, "(A(A(A))")

        self.assertEqual("", remove_redundant_parentheses("()"))
        self.assertEqual("ABC", remove_redundant_parentheses("(ABC)"))
        self.assertEqual("ABC", remove_redundant_parentheses("((ABC))"))
        self.assertEqual("1+2", remove_redundant_parentheses("(1)+(2)"))
        self.assertEqual("1+2", remove_redundant_parentheses("(1+2)"))
        self.assertEqual("1+2+2", remove_redundant_parentheses("(1+2)+2"))
        self.assertEqual("(1+2)*2", remove_redundant_parentheses("(1+2)*2"))
        self.assertEqual("(A+B)*C", remove_redundant_parentheses("(A+B)*C"))
        self.assertEqual("A*B+C", remove_redundant_parentheses("(A*B)+C"))
        self.assertEqual("C*(A+B)", remove_redundant_parentheses("C*(A+B)"))
        self.assertEqual("C+A*B", remove_redundant_parentheses("C+(A*B)"))
        self.assertEqual("A*(A*B+C)", remove_redundant_parentheses("A*((A*B)+C)"))
        self.assertEqual("A+A*B+C", remove_redundant_parentheses("A+((A*B)+C)"))
        self.assertEqual("A+A*B+C", remove_redundant_parentheses("A+((A*B)+C)"))
        self.assertEqual("A+A+B+C", remove_redundant_parentheses("A+(A+B)+C"))
        self.assertEqual("A+A*B+C", remove_redundant_parentheses("A+(A*B)+C"))
        self.assertEqual("A+(A+B)*C", remove_redundant_parentheses("A+(A+B)*C"))
        self.assertEqual("A*(A+B)+C", remove_redundant_parentheses("A*(A+B)+C"))
        self.assertEqual("max{max2{+5+14+5+12}}", remove_redundant_parentheses("max{max2{+(5+14+5+12)}}"))

    def __show_exec_res(self, exp_str: str):
        for _ in range(100):
            exec_roll_exp(exp_str)
        res = exec_roll_exp(exp_str)
        self.assertIsNotNone(res)
        output = f"Values: {res.val_list} \tInfo: {res.get_info()} \tType: {res.type} \tExpression: {res.get_exp()}"
        output += f"\nFinal Output: \033[0;33m{res.get_exp()} = {res.get_result()}"

        print("\t\t--- Check Result ---")
        print(f"Origin Exp: \033[0;32m{exp_str} \033[0m\t{output}")

    def __show_exception(self, exp_str: str):
        self.assertRaises(RollDiceError, exec_roll_exp, exp_str)
        try:
            exec_roll_exp(exp_str)
        except RollDiceError as e:
            print("\t\t--- Check Exception ---")
            print(f"Origin Exp: \033[0;35m{exp_str} \t\033[0;33m{e.info}")

    def test_basic_roll(self):
        # 基础情况
        self.__show_exec_res("1D20")
        self.__show_exec_res("3D20")
        self.__show_exec_res("D")
        self.__show_exec_res("1D")
        self.__show_exec_res("D4")
        self.__show_exec_res("1")
        self.__show_exec_res("+1D20")
        self.__show_exec_res("-1D20")

        # 基础运算
        self.__show_exec_res("1D20+1")
        self.__show_exec_res("1D20-1")
        self.__show_exec_res("3D20*2")
        self.__show_exec_res("3D20/2")
        self.__show_exec_res("1+1D20")
        self.__show_exec_res("1-1D20")
        self.__show_exec_res("2*3D20")
        self.__show_exec_res("2/3D20")

        # 带空格和中文字符情况 (由于判断指令中表达式和掷骰原因的问题去掉了过滤空格的代码)
        self.__show_exec_res("1d20")
        self.__show_exec_res("d20＋1")
        # self.__show_exec_res(" 1 D 2 0 ")
        # self.__show_exec_res("1D20 ＋ 1")

        # 带修饰符情况
        self.__show_exec_res("2D20k1")
        self.__show_exec_res("1D20K2")
        self.__show_exec_res("4D20k2kl1")
        self.__show_exec_res("4D20r<10")
        self.__show_exec_res("4D20x<10")
        self.__show_exec_res("4D20xo<10")
        self.__show_exec_res("4D20r<10x>10")
        self.__show_exec_res("4D20x>10r<10")

        # 带括号
        self.__show_exec_res("(1+2)")
        self.__show_exec_res("(1+2)*2")
        self.__show_exec_res("(D20)*2")
        self.__show_exec_res("(1+D20)*2")
        self.__show_exec_res("((1+D20))*2")
        self.__show_exec_res("(D20)")
        self.__show_exec_res("(D20)*(D20)")

        # 优势与劣势
        self.__show_exec_res("D20优势")
        self.__show_exec_res("D20劣势+1")
        self.__show_exec_res("D20劣势+1+D优势")
        self.__show_exception("2D20优势")
        self.__show_exception("2D20优势+1")
        self.__show_exception("1+20优势")

        # 非法输入
        self.__show_exception("")
        self.__show_exception("()")
        self.__show_exception("1D(20)")
        self.__show_exception("(1)D20")
        self.__show_exception("1(D)20")
        self.__show_exception("1++1")
        self.__show_exception("1+1+")
        self.__show_exception("+")
        self.__show_exception("*")
        self.__show_exception("(D20")
        self.__show_exception("D20)")
        self.__show_exception("(D20)+(1")
        self.__show_exception("((D20)+1))))")

        # 边界条件
        self.__show_exception(f"1D{roll_config.DICE_TYPE_MAX + 1}")
        self.__show_exception(f"{roll_config.DICE_NUM_MAX + 1}D20")
        self.__show_exception(f"{roll_config.DICE_CONSTANT_MIN - 1}")
        self.__show_exception(f"{roll_config.DICE_CONSTANT_MAX + 1}")

    def test_d20_state(self):
        # 测试大成功或大失败是否可以生效
        def repeat_until_checked(exp_str: str) -> bool:
            exp: RollExpression = parse_roll_exp(preprocess_roll_exp(exp_str))
            has_succ, has_fail = False, False
            for _ in range(1000):
                res: RollResult = exp.get_result()
                if res.d20_num == 1:
                    if res.d20_state == 20:
                        has_succ = True
                    elif res.d20_state == 1:
                        has_fail = True
                if has_succ and has_fail:
                    return True
            return False

        self.assertTrue(repeat_until_checked("D20"))
        self.assertTrue(repeat_until_checked("2D20KL1"))
        self.assertTrue(repeat_until_checked("2D20K1"))
        self.assertTrue(repeat_until_checked("1D20K3"))
        self.assertTrue(repeat_until_checked("1D4+1D20+20"))

        self.assertTrue(not repeat_until_checked("2D20"))
        self.assertTrue(not repeat_until_checked("4D20K3"))
        self.assertTrue(not repeat_until_checked("D20+D20"))


if __name__ == '__main__':
    unittest.main()
