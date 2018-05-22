import argparse
import os.path as op
import pickle

from recon.tacst_parser import TacStParser
from recon.recon import FILES, Recon


"""
[Note]

1. Visualize all files
    python ml4tp/visualize.py all
2. Visualize a lemma in a specific file
    python ml4tp/visualize.py <file> -l <lemma>
"""


class Visualize(object):
    def __init__(self, f_display=False, f_jupyter=False, f_verbose=False,
                 tactr_file="tactr.log"):
        # Internal book-keeping
        self.recon = Recon()         # tactic tree reconstructor
        self.tactrs = []             # reconstructed tactic trees
        self.failed = []             # failed reconstructions

        # Flags
        self.f_display = f_display   # draw graph?
        self.f_jupyter = f_jupyter   # using jupyter?
        self.f_verbose = f_verbose   # verbose?

        # Tactic tree statistics
        self.tactr_file = tactr_file
        self.h_tactr_file = open(tactr_file, 'w')
        self.h_tactr_file.write("LEMMA INFO\n")
        self.num_iargs = 0
        self.num_args = 0

    def finalize(self):
        self.h_tactr_file.write("TOTAL: {} WERID: {}\n".format(
                                len(self.tactrs), len(self.failed)))
        self.h_tactr_file.write("UNIQUE-SORT: {}\n".format(
                                len(self.recon.embed_tokens.unique_sort)))
        self.h_tactr_file.write("UNIQUE-CONST: {}\n".format(
                                len(self.recon.embed_tokens.unique_const)))
        self.h_tactr_file.write("UNIQUE-IND: {}\n".format(
                                len(self.recon.embed_tokens.unique_ind)))
        self.h_tactr_file.write("UNIQUE-CONID: {}\n".format(
                                len(self.recon.embed_tokens.unique_conid)))
        self.h_tactr_file.write("UNIQUE-EVAR: {}\n".format(
                                len(self.recon.embed_tokens.unique_evar)))
        self.h_tactr_file.write("UNIQUE-FIX: {}\n".format(
                                len(self.recon.embed_tokens.unique_fix)))
        self.h_tactr_file.write("NUM_IARGS: {}\n".format(self.num_iargs))
        self.h_tactr_file.write("NUM_ARGS: {}\n".format(self.num_args))
        self.h_tactr_file.close()

    def save_tactrs(self):
        with open("tactr.pickle", 'wb') as f:
            pickle.dump(self.tactrs, f)

    def load_tactrs(self):
        with open("tactr.pickle", 'rb') as f:
            self.tactrs = pickle.load(f)

    def test_parse_tac(self, file):
        ts_parser = TacStParser(file)
        ts_parser.parse_file()

    def visualize_file(self, file):
        tactrs = self.recon.recon_file(file, not self.f_jupyter)
        self.tactrs += tactrs
        
        for tactr in tactrs:
            succ, ncc = tactr.check_success()
            if not succ:
                print("FAILED", tactr.name, ncc)
                self.failed += [(file, tactr.name, ncc, len(tactr.notok))]

            info = tactr.log_stats(self.h_tactr_file)
            self.num_iargs += info['hist_gc'][1]
            self.num_args += info['hist_gc'][2]
            print("iargs / args = {} / {}".format(self.num_iargs, self.num_args))

    def visualize_lemma(self, file, lemma):
        tactr = self.recon.recon_lemma(file, lemma, not self.f_jupyter)
        self.tactrs += [tactr]

        if self.f_display:
            if self.f_jupyter:
                tactr.show_jupyter()
            else:
                tactr.show()
        return tactr


if __name__ == "__main__":
    # Set up command line
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file",
                           help="Enter the file you want to visualize.")
    argparser.add_argument("-d", "--display", action="store_true",
                           help="Display the tactic tree.")
    argparser.add_argument("-l", "--lemma", type=str,
                           help="Visualize a specific lemma by name.")
    argparser.add_argument("-p", "--path", default="data/odd-order",
                           type=str, help="Path to files")
    argparser.add_argument("-to", "--tactrout", default="tactr.log", type=str,
                           help="Compute tactic tree statistics")
    argparser.add_argument("-v", "--verbose", action="store_true",
                           help="Verbose")
    args = argparser.parse_args()

    files = [op.join(args.path, file) for file in FILES]
    bgfiles = [op.join(args.path, file) for file in
               FILES if file.startswith("BG")]
    pffiles = [op.join(args.path, file) for file in
               FILES if file.startswith("PF")]

    # Visualize
    vis = Visualize(f_display=args.display, f_verbose=args.verbose,
                    tactr_file=args.tactrout)
    if args.lemma:
        file = op.join(args.path, args.file)
        vis.test_parse_tac(file)
    else:
        if args.file == "all":
            for file in files:
                vis.visualize_file(file)
        elif args.file == "bg":
            for file in bgfiles:
                vis.visualize_file(file)
        elif args.file == "pf":
            for file in pffiles:
                vis.visualize_file(file)
        else:
            file = op.join(args.path, args.file)
            vis.visualize_file(file)
        vis.finalize()
        vis.save_tactrs()