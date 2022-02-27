import json
import io
import logging
import argparse
from random import choice


class FlashCards:

    msg = {'card_trm': f'The card:',
           'card_def': f'The definition of the card:',
           'card_add': lambda trm, def_: f'The pair ("{trm}":"{def_}") has been added.\n',
           'del_trm': f'Which card?\n',
           'del_ok': f'The card has been removed.\n',
           'del_fail': lambda trm: f"""Can't remove "{trm}": there is no such card.\n""",
           'file_name': 'File name:\n',
           'no_file': 'File not found.\n',
           'file_saved': 'The log has been saved.\n',
           'cards_loaded': lambda n: f'{n} cards have been loaded.\n',
           'cards_saved': lambda n: f'{n} cards have been saved.\n',
           'how_many': 'How many times to ask?\n',
           'print_def': lambda trm: f'Print the definition of "{trm}":\n',
           'wrong': lambda def_: f'Wrong. The right answer is "{def_}"',
           'wrong_but': lambda trm: f', but your definition is correct for "{trm}"',
           'correct': 'Correct!',
           'trm_exists': lambda trm: f'The card "{trm}" already exists. Try again:',
           'def_exists': lambda def_: f'The definition "{def_}" already exists. Try again:',
           'inp_action': lambda act: f'Input the action ({", ".join(act)}):\n',
           'hardest_card': lambda cards, errors: f"""The hardest card{" is" if len(cards) == 1 else "s are"} {", ".join(map(lambda x: f'"{x}"', cards))}."""
                                                 f' You have {errors} errors answering {"it" if len(cards) == 1 else "them"}.\n',
           'no_errors': 'There are no cards with errors.\n',
           'reset_stats': 'Card statistics have been reset.\n',
           'on_exit': 'Bye bye!'}

    def __init__(self):
        self.cards = {}
        self.cards_stats = {}
        self.imp_file_name = None
        self.exp_file_name = None
        self.logger = logging.getLogger()
        self.buffer = io.StringIO()
        self.setup_logger()
        self.get_args()
        self.actions = {'add': 'self.create_card()',
                        'remove': 'self.delete_card()',
                        'import': 'self.import_cards()',
                        'export': 'self.export_cards()',
                        'ask': 'self.quiz()',
                        'exit': '-1',
                        'log': 'self.save_log()',
                        'hardest card': 'self.hardest_card()',
                        'reset stats': 'self.reset_stats()'}

    def setup_logger(self):
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler(self.buffer))

    def get_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--import_from', default=None)
        parser.add_argument('--export_to', default=None)
        args = parser.parse_args()
        self.imp_file_name = args.import_from
        self.exp_file_name = args.export_to
        if self.imp_file_name:
            self.import_cards()

    def print_and_log(self, msg):
        print(msg)
        self.logger.info(msg)

    def input_and_log(self, msg=None):
        inp = input(msg if msg else '')
        self.logger.info(f'{msg}{inp}' if msg else inp)
        return inp

    def save_log(self):
        with open(input(self.msg['file_name']), 'a') as file:
            file.write(self.buffer.getvalue())
        print(self.msg['file_saved'])

    def get_unique(self, set_, msg, msg_if_exist):
        self.print_and_log(msg)
        while True:
            inp = self.input_and_log()
            if inp not in set_:
                return inp
            self.print_and_log(msg_if_exist(inp))

    def create_card(self):
        term = self.get_unique(self.cards, self.msg['card_trm'], self.msg['trm_exists'])
        definition = self.get_unique(self.cards.values(), self.msg['card_def'], self.msg['def_exists'])
        self.cards[term] = definition
        self.print_and_log(self.msg['card_add'](term, definition))

    def delete_card(self):
        term = self.input_and_log(self.msg['del_trm'])
        if term not in self.cards:
            return self.print_and_log(self.msg['del_fail'](term))
        self.cards.pop(term)
        self.print_and_log(self.msg['del_ok'])

    def export_cards(self):
        file_name = self.exp_file_name if self.exp_file_name else self.input_and_log(self.msg['file_name'])
        with open(file_name, 'w') as file:
            json.dump(self.cards, file)
        self.print_and_log(self.msg['cards_saved'](len(self.cards)))

    def import_cards(self):
        try:
            file_name = self.imp_file_name if self.imp_file_name else self.input_and_log(self.msg['file_name'])
            with open(file_name, 'r') as file:
                imported_cards = json.load(file)
                self.cards.update(imported_cards)
            self.print_and_log(self.msg['cards_loaded'](len(imported_cards)))
        except FileNotFoundError:
            self.print_and_log(self.msg['no_file'])

    def check(self, trm, inp, def_):
        if inp == def_:
            self.print_and_log(self.msg['correct'])
        else:
            self.cards_stats.setdefault(trm, 0)
            self.cards_stats[trm] += 1
            if inp in self.cards.values():
                trm = list(self.cards)[list(self.cards.values()).index(inp)]
                self.print_and_log(f'{self.msg["wrong"](def_)}{self.msg["wrong_but"](trm)}.\n')
            else:
                self.print_and_log(f'{self.msg["wrong"](def_)}.\n')

    def quiz(self):
        for _ in range(int(self.input_and_log(self.msg['how_many']))):
            trm = choice(list(self.cards))
            inp = self.input_and_log(self.msg['print_def'](trm))
            self.check(trm, inp, self.cards[trm])

    def hardest_card(self):
        if not self.cards_stats:
            self.print_and_log(self.msg['no_errors'])
        else:
            max_errors = max(self.cards_stats.values())
            hardest_cards = [key for key, value in self.cards_stats.items() if value == max_errors]
            self.print_and_log(self.msg['hardest_card'](hardest_cards, max_errors))

    def reset_stats(self):
        self.cards_stats = {}
        self.print_and_log(self.msg['reset_stats'])

    def run(self, exit_=None):
        while not exit_:
            exit_ = eval(self.actions[self.input_and_log(self.msg['inp_action'](self.actions))])
        self.print_and_log(self.msg['on_exit'])
        if self.exp_file_name:
            self.export_cards()


def main():
    flash_cards = FlashCards()
    flash_cards.run()


if __name__ == '__main__':
    main()
