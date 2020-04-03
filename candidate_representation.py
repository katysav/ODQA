import torch
from torch import nn
import torch.nn.functional as F


class Candidate_Represenation():
    '''
    Condense and interconnect candidates from different
    passages in order to improve the selection of an answer among them.
    '''

    def __init__(self, S_p, spans, k=2):
        print('Started Candidate Representation.')
        self.S_p = S_p
        self.spans = spans
        self.k = k
        self.M = spans.shape[0]*k #num_passages * num_candidates
        self.wb = torch.randn(200, 200) #dimension candidate * dimension s
        self.we = torch.randn(200, 200)
        # Linear transformations to capture the intensity
        # of each interaction (used for the attention mechanism)
        self.wc = torch.randn(200, 200)
        self.wo = torch.randn(200, 200)
        self.wv = torch.randn(1, 200)
        self.S_Cs, self.r_Cs = self.calculate_condensed_vector_representation()
        self.V = self.calculate_correlations()
        self.tilda_r_Cs = self.generate_fused_representation()

    def calculate_condensed_vector_representation(self):
        '''
        Returns the condensed vector representation of all candidates by condensing their start and end tokens.
        :return:
        '''
        sp_cb = []
        sp_ce = []
        S_Cs = []
        start_indices = self.spans[:, :, 0]
        end_indices = self.spans[:, :, 1]
        max_seq_len = self.S_p.shape[1]  # padding length

        # todo: check if shape[0] really is the number of candidates
        for p in range(self.S_p.shape[0]):
            # Iterate through the candidates per passage
            for i in range(self.k):
                # Start and end tokens of candidate
                sp_cb.append(self.S_p[p][start_indices[p][i]]) # Candidate Nr. i start
                sp_ce.append(self.S_p[p][end_indices[p][i]])
                '''
                Full candidate
                Pad candidate to full length, but keep position relative to full passage
                Example p=[a,b,c,d], c=[b,c] => S_C=[0,b,c,0]
                '''
                c = self.S_p[p][start_indices[p][i]:end_indices[p][i]]
                num_start_pads = start_indices[p][i]
                num_end_pads = max_seq_len - num_start_pads - c.shape[0]
                S_C = F.pad(input=c, pad=(0, 0, num_start_pads, num_end_pads), mode='constant', value=0)
                S_Cs.append(S_C)

        # Stack to turn into tensor
        sp_cb = torch.stack(sp_cb, dim=0) #(200x200)
        sp_ce = torch.stack(sp_ce, dim=0) #(200x200)
        # todo: Reshpae S_C to (200x100x100)
        S_Cs = torch.stack(S_Cs, dim=0)
        # Calculate r_c
        # todo: warning I changed bmm
        b = torch.mm(self.wb, sp_cb) #sp_cb is
        e = torch.mm(self.we, sp_ce)
        r_Cs = torch.add(b, e).tanh()

        return S_Cs, r_Cs

 

    def calculate_correlations(self):
        '''
        Model the interactions via attention mechanism.
        Returns a correlation matrix
        '''
        #r_Cs = torch.split(self.r_c, 100, dim=0) # TODO: check the dimensions

        V_jms = []

        for i, r_C in enumerate(self.r_Cs):
            rcm = torch.cat([self.r_Cs[0:i], self.r_Cs[i+1:]], dim=0)
            c = torch.mm(self.wc, r_C.view(-1,1))
            o = torch.mm(self.wo, rcm.t()) #transpose because first dimensions is 199 instead of 200
            V_jm = torch.mm(self.wv, torch.add(c, o).tanh())
            V_jms.append(V_jm)

        V = torch.stack(V_jms, dim=0) #(200x1x199) # should we reshape this to M*M? #V = V.view((self.M,self.M))
        V = V.view(-1, self.M-1) #(200x199)
        print('Final v shape', V.shape)
        return V


    def generate_fused_representation(self):
        # Normalize interactions
        #V_jms = torch.split(V, ..., dim=0) # TODO: check the dimensions

        alpha_ms = []
        for i, V_jm in enumerate(self.V):
            numerator = torch.exp(V_jm)
            denominator_correlations = torch.cat([self.V[0:i], self.V[i:]], dim=0)
            # todo: this throws an error if i is 0
            #denominator_correlations = torch.stack([self.V[0:i], self.V[i:]], dim=0)
            denominator = torch.sum(torch.exp(denominator_correlations), dim=0)
            alpha_m = torch.div(numerator, denominator)
            alpha_ms.append(alpha_m)

        alpha = torch.stack(alpha_ms, dim=0)
        print(alpha.shape, 'alpha shape')
        # Generate fused representations
        #r_Cs = torch.split(self.rC, 100, dim=0) # TODO: check the dimensions

        tilda_rсms = []

        for i, r_C in enumerate(self.r_Cs):
            # todo: I changed this please double check. I think the sum is taken for every individual candidate so it is taken M times
            rcm = torch.cat([self.r_Cs[0:i], self.r_Cs[i+1:]], dim=0) #maybe alpha is multiplied
            alpha_m = torch.cat([alpha[0:i], alpha[i+1:]], dim=0)
            tilda_rсm = torch.sum(torch.mm(alpha_m, rcm)) # todo: changed from bmm to mm
            tilda_rсms.append(tilda_rсm)

        #tilda_rcms = torch.stack(tilda_rcms, dim=0)
        #tilda_rC = torch.sum(tilda_rcms) # sum for every candidate so we should have M values
        #return tilda_rC
        return torch.stack(tilda_rсms, dim=0)