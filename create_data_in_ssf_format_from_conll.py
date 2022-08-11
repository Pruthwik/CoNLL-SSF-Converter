"""Convert data into SSF format from CoNLL format for files."""
import re
import argparse
import os
from string import punctuation


# Punctuation Markers 
punc_markers = set(';,"।\'')
# Symbols other than punctuation markers
symbols = set(punctuation) - punc_markers


def read_lines_from_file(file_path):
    '''
    Read lines from a file.
    :param file_path: Path of the file
    :return lines: Lines read from the file
    '''
    with open(file_path, 'r', encoding='utf-8') as file_read:
        return file_read.readlines()


def create_data_in_ssf_from_conll_lines(lines, opr=0):
    '''
    Read a feature file and convert it into SSF format.
    :param file_path: File Path
    :param opr: Operation type, 1 for Chunk and 0 for POS
    :return: None
    '''
    final_string = ''
    sent_count = 1
    cntr = 1
    sent_string = ''
    prev_tag = ''
    prev_sent_count = 0
    # opr = 1 is for Chunking
    if opr == 1:
        sent_string += "<Sentence id='" + str(sent_count) + "'>\n"
        for line in lines:
            if line.strip() != '':
                features = line.strip().split('\t')
                chnk_info = features[2].split('-')
                if re.search('B-', features[2]) is not None:
                    subcntr = 1
                    if prev_sent_count != sent_count:
                        sent_string += str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                        prev_sent_count = sent_count
                    else:
                        cntr += 1
                        sent_string += '\t))\n' + str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
                elif re.search('I-' + prev_tag, features[2]) is not None:
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
                if prev_tag != chnk_info[1] and chnk_info[0] == 'I':
                    subcntr = 1
                    cntr += 1
                    sent_string += '\t))\n' + str(cntr) + '\t((\t' + chnk_info[1] + '\t\n'
                    sent_string += str(cntr) + '.' + str(subcntr) + '\t' + features[0] + '\t' + features[1] + '\t\n'
                    subcntr += 1
                    prev_tag = chnk_info[1]
            else:
                sent_string += "\t))\n</Sentence>\n"
                final_string += sent_string + '\n'
                sent_count += 1
                sent_string = "<Sentence id='" + str(sent_count) + "'>\n"
                cntr = 1
                subcntr = 1
    else:
        # This part is for POS Tagging.
        sent_string += "<Sentence id='" + str(sent_count) + "'>\n"
        for line in lines:
            if line.strip() != '':
                features = line.strip().split('\t')
                sent_string += str(cntr) + '\t' + features[0] + '\t' + features[-1] + '\t\n'
                cntr += 1
            else:
                sent_string += '</Sentence>\n'
                final_string += sent_string + '\n'
                sent_count += 1
                cntr = 1
                sent_string = "<Sentence id='" + str(sent_count) + "'>\n"
    return final_string


def update_incorrect_chunk_tags(lines):
    '''
    Update incorrect chunk tags.
    :param lines: CoNLL lines
    :return updated_lines: Updated lines after correcting chunk tags.
    '''
    updated_lines = list()
    prev_label, prev_type = '', ''
    for line in lines:
        if line.strip():
            token, pos_tag, chunk_tag = line.strip().split('\t')
            if token in symbols:
                pos_tag = 'RD_SYM'
                line = '\t'.join([token, pos_tag, chunk_tag]) + '\n'
            if token in punc_markers:
                pos_tag = 'RD_PUNC'
                line = '\t'.join([token, pos_tag, chunk_tag]) + '\n'
            chunk_label, chunk_type = chunk_tag.split('-')
            if not prev_label and not prev_type:
                if chunk_label == 'I':
                    updated_lines.append(token + '\t' + pos_tag + '\t' + 'B-' + chunk_type + '\n')
                    prev_label = 'B'
                else:
                    updated_lines.append(line)
                    prev_label = chunk_label
                prev_type = chunk_type
            else:
                if chunk_label != prev_label and chunk_type == prev_type:
                    updated_lines.append(line)
                    prev_label = chunk_label
                    prev_type = chunk_type
                elif chunk_type != prev_type and chunk_label == 'I':
                    updated_lines.append(token + '\t' + pos_tag + '\t' + 'B-' + chunk_type + '\n')
                    prev_label = 'B'
                    prev_type = chunk_type
                else:
                    updated_lines.append(line)
                    prev_label = chunk_label
                    prev_type = chunk_type
        else:
            updated_lines.append(line)
            prev_label, prev_type = '', ''
    return updated_lines


def convert_feature_files_into_ssf_format(input_folder_path, output_folder_path, opr=0):
    '''
    :param input_folder_path: Input Folder Path
    :param output_folder_path: Output Folder Path
    '''
    for root, dirs, files in os.walk(input_folder_path):
        for fl in files:
            input_file_path = os.path.join(root, fl)
            input_lines = read_lines_from_file(input_file_path)
            if opr:
                corrected_lines = update_incorrect_chunk_tags(input_lines)
            else:
                corrected_lines = input_lines
            ssf_text = create_data_in_ssf_from_conll_lines(corrected_lines, opr)
            output_path = os.path.join(output_folder_path, fl)
            write_text_to_file(ssf_text, output_path)


def write_text_to_file(text, out_path):
    '''
    :param text: Text to be written to file
    :param out_path: Enter the path of the output file
    :return: None
    '''
    with open(out_path, 'w', encoding='utf-8') as file_write:
        file_write.write(text + '\n')


def main():
    '''
    Pass arguments and call functions here.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='inp', help="Add the input folder path of conll files.")
    parser.add_argument('--output', dest='out', help="Add the output folder path where conll files will be converted into SSF format.")
    parser.add_argument('--opr', dest='opr', help="Add the operation 0 pos tagging 1 chunking", type=int, choices=[0, 1])
    args = parser.parse_args()
    if not os.path.isdir(args.out):
        os.makedirs(args.out)
    convert_feature_files_into_ssf_format(args.inp, args.out, args.opr)


if __name__ == '__main__':
    main()

