import torch
from torch.utils.data import Dataset, DataLoader

MAX_SEQUENCE_LENGTH = 100

class question_answer_set(Dataset):
    '''
    Store and load data for training and testing. This can be used to
    create minibatches.
    '''


    def __init__(self, file_content):
        # todo: implement a max size parameter to allow for mini-sets, it should stop reading in content when
        # reaching max_size
        # Questions
        self.questions = None
        self.question_lengths = None
        # Contexts
        self.contexts = None
        self.context_lengths = None
        # Answers
        self.answers = None
        self.answer_lengths = None
        # Type of Tensor
        self.longtype = torch.int64
        # Length of dataset (number of question_context_answer pairs)
        self.set_len = None
        self.read_in_dataset(file_content)


    def read_in_dataset(self, content):
        '''
        :param
        :return:
        '''
        question_context_answer_pairs = []
        self.set_len = None

        # Read q,c,a and convert to a torch tensor
        # todo: ensure that this torch tensor is of self.LongType
        for item in content:
            item_id = item
            question = content[item_id]['encoded_question']
            contexts = content[item_id]['encoded_contexts']
            answer = content[item_id]['encoded_answer']
            for context in contexts:
                question_context_answer_pairs.append([question, context, answer])

        self.set_len = len(question_context_answer_pairs)
        # Initialize empty matrices
        self.questions = torch.zeros(self.set_len, MAX_SEQUENCE_LENGTH,dtype=self.longtype)
        self.question_lengths = torch.zeros(self.set_len,dtype=self.longtype)
        self.contexts = torch.zeros(self.set_len, MAX_SEQUENCE_LENGTH,dtype=self.longtype)
        self.context_lengths = torch.zeros(self.set_len,dtype=self.longtype)
        self.answers = torch.zeros(self.set_len, MAX_SEQUENCE_LENGTH,dtype=self.longtype)
        self.answer_lengths = torch.zeros(self.set_len, MAX_SEQUENCE_LENGTH,dtype=self.longtype)

        # Update the matrices
        # note: inefficient, stores questions and answers multiple times
        for idx, (q, c, a) in enumerate(question_context_answer_pairs):
            # Update embedding matrices
            self.questions[idx] = torch.from_numpy(q)
            self.contexts[idx] = torch.from_numpy(c)
            self.answers[idx] = torch.from_numpy(a)

            # Update length matrices
            #self.question_lengths[idx] = list(torch.shape(torch.nonzero(q)))[1]
            #self.context_lengths[idx] = list(torch.shape(torch.nonzero(c)))[1]
            #self.answer_lengths[idx] = list(torch.shape(torch.nonzero(a)))[1]
            print(q, c, a)
            self.question_lengths[idx] = len(q[a.nonzero()])
            self.context_lengths[idx] = len(c[a.nonzero()])
            self.answer_lengths[idx] = len(a[a.nonzero()])

    def __getitem__(self, index):
        '''
        Returns a single question, context, answer pair and the corresponding
        lenghts (lengths exclude padding)
        :param index:
        :return:
        '''
        # todo: could we calculate the lengths on the fly within getitem?
        return self.questions[index], self.contexts[index], self.answers[index], self.question_lengths[idx], self.context_lengths[idx], self.answer_lengths[idx]


    def __len__(self):
        return self.set_len