import torch
from praatio import textgrid
import json

with open("data_test.json", "r") as f:
    data = json.load(f)


class AlignmentEvaluator:
    def __init__(self, json_path, mfa_path):

        with open(json_path, "r") as f:
            self.gt = json_path
        
        self.mfa = mfa_path

    def find_sequence_intervals(interval_data, sequence):
        sequence_length = len(sequence)
        results = []

        for i in range(len(interval_data) - sequence_length + 1):
            window = interval_data[i: i + sequence_length]
            words_in_window = [entry["word"] for entry in window]
        
            if words_in_window == sequence:
                interval_start = window[0]["start"]
                interval_end = window[-1]["end"]
                results.append(
                    {"start": interval_start,
                     "end": interval_end,
                     "words": words_in_window}
                     )
    
        return results
    

    def get_intervals(textgrid_path):
        """Given a path to a Textgrid file of MFA aligned audio, get
        the time intervals for each word.
        """
        # Load the TextGrid file
        tg = textgrid.openTextgrid(textgrid_path, includeEmptyIntervals=True)

        interval_data = []
        # Extract the time alignments
        for interval in tg.tiers[0].entries:
            start_time, end_time, label = interval
            interval_data.append(
                {"start": start_time,
                 "end": end_time,
                "word": label})
            
        return interval_data
    

    def get_tensor_frames(sampling_rate, t):
        """Given a sampling rate, convert a time of that audio to the 
        corresponding frames in an audio tensor with that same sampling rate."""

        t_frame = int(t * sampling_rate)
        return t_frame


    def get_mask_from_bounding_box(T, bounding_box):
        tensor = torch.zeros_like(T)
        mask = torch.zeros(T.size[1], T.size[2])
        mask[bounding_box] = 1

        return tensor * mask
        

    def get_alignment_score_object(self, tensor, start, end, bounding_box):
        """Calculate the alignment score for objects as in
        Khorrami & Rasanen, 2021.
        """

        # Normalize each frame of the tensor to sum to 1
        frame_sums = tensor.sum(dim=(1, 2), keepdim=True)
        T = tensor / frame_sums

        return T[start:end, bounding_box].sum() / (end - start)

    
    def get_alignment_score_word(self, tensor, start, end, bounding_box):
        """Calculate the alignment score for words as in
        Khorrami & Rasanen, 2021.
        """

        # Normalize each frame of the tensor to sum to 1
        T = tensor / tensor.sum()

        return T[start:end, bounding_box].sum() / bounding_box.sum()
    
    def get_glancing_score_object(self, tensor, start, end, bounding_box):
        """Calculate the glancing score for objects as in
        Khorrami & Rasanen, 2021.
        """
        A = tensor[start:end].sum(axis=0)
        A = A / A.sum()

        mask = self.get_mask_from_bounding_box(bounding_box)
        return (A * mask).sum()

    
    def get_glancing_score_word(self, tensor, start, end, bounding_box):
        """Calculate the glancing score for words as in
        Khorrami & Rasanen, 2021.
        """
        mask = self.get_mask_from_bounding_box(bounding_box)
        a = (tensor * mask).sum(axis=0)
        a = a / a.sum()
        
        return a[start:end]
