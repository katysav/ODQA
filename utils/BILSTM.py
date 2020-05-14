import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence as pack
from torch.nn.utils.rnn import pad_packed_sequence as unpack

class BiLSTM(nn.Module):
    def __init__(self, embedding_matrix, embedding_dim, hidden_dim, dropout=0.1):
        super(BiLSTM, self).__init__()

        #what about cuda? where do we need to specify GPU?
        #might need to add more parameters as we will have more features in later stages - advanced representations
        self.embeddings = embedding_matrix
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.embedding = nn.Embedding.from_pretrained(torch.FloatTensor(self.embeddings))
        self.dropout = dropout #try without dropout too and with different p
        self.bilstm = nn.LSTM(input_size=embedding_dim, hidden_size=hidden_dim, dropout=self.dropout, bidirectional=True)
        #self.hidden2label = nn.Linear(hidden_dim, ?) #define second dimension - target length k?

    def embed(self, sentence):
        return self.embedding(sentence)

    def forward(self, sentence, sentence_lengths):
        packed_x = pack(self.embedding(sentence), sentence_lengths, batch_first=True, enforce_sorted=False)
        lstm_out, _ = self.bilstm(packed_x)
        lstm_out, lstm_out_lengths = unpack(lstm_out, total_length=100, batch_first=True)
        return lstm_out

def max_pooling(input_tensor, max_sequence_length):
    # Not in BiLSTM because as of now the BiLSTM class only works for embedding inputs
    mxp = nn.MaxPool2d((max_sequence_length, 1),stride=1)
    return mxp(input_tensor)


def attention(questions, contexts):
    max_value = torch.max(torch.max(torch.bmm(questions, torch.transpose(contexts, 1, 2))))
    numerator = torch.exp(torch.bmm(questions, torch.transpose(contexts, 1, 2)) - max_value)
    denominator = torch.sum(numerator)#, dim=1).view(numerator.shape[0], 1, numerator.shape[2]) #this cannot be just a single number.It must at least have t values since we have t words in a passage.
    print('attention nominator shape', numerator.shape)
    print('attention denominator', denominator.shape)
    alpha_tk = torch.div(numerator,denominator) #->dim 54,54
    #alpha_tk = nn.Softmax()(numerator)
    #print(alpha_tk)
    print('Sum alpha_tk', torch.sum(alpha_tk), alpha_tk.shape)
    

    h_tP = torch.bmm(alpha_tk, questions) #->dim 1,300

    #H_P = torch.cat(, dim=0) #dim -> 54,300
    #is h_tP already H_P?
    H_P = h_tP # for now
    print('sum attention', torch.sum(H_P))
    return H_P

'''
def attention(all_questions, all_contexts):
    # assuming that input for question and context has dim 54x300 respectively and not 54x1x300

    def attention_sub(question, context):print(f'shapes {question.shape}, {context.shape}')
        # assuming that input for question and context has dim 54x300 respectively and not 54x1x300
        max_value = torch.max(torch.bmm(question, torch.transpose(context, 1, 2)))

        numerator = torch.exp(torch.bmm(question, torch.transpose(context, 1, 2))- max_value) 
        denominator = torch.sum(numerator) #index 0?

        alpha_tk = torch.div(numerator,denominator) #->dim 54,54


        h_tP = torch.bmm(alpha_tk, question) #->dim 1,300
     
        return H_P

    H_Ps = []
    for c in all_contexts:
        H_Ps.append(attention_sub(all_questions[0], c))
    H_Ps = torch.stack(H_Ps, dim=0)
    print(f'H_P shape is {H_Ps.shape}')
    return H_Ps


'''





'''
def attention(all_questions, all_contexts):
    # assuming that input for question and context has dim 54x300 respectively and not 54x1x300

    def attention_sub(question, context):
        question = question.view(question.shape[0], 1, 200)
        context = context.view(1, context.shape[0], 200)
        numerator = torch.exp(question*context)
        denominator = torch.sum(numerator, dim=0)
        alphas = numerator/denominator
        
        H_P = []
        for i in range(alphas.shape[0]):
            H_P.append(torch.sum(alphas[i]*question[i], dim=0))
            
        H_P = torch.stack(H_P, dim=0)
        return H_P

    H_Ps = []
    for c in all_contexts:
        H_Ps.append(attention_sub(all_questions[0], c))
    H_Ps = torch.stack(H_Ps, dim=0)
    print(f'H_P shape is {H_Ps.shape}')
    return H_Ps
'''
