from .rcrd_record import OperationCode


class Transaction():
    def __init__(self, kickoff_tuple):
        self.hc_tuples = [kickoff_tuple]
        self.transaction_num = None

    def prepend(self, hc_tuple):
        self.hc_tuples.insert(0, hc_tuple)

    def append(self, hc_tuple):
        self.hc_tuples.append(hc_tuple)

    @property
    def length(self):
        return len(self.hc_tuples)

    @property
    def mft_key(self):
        try:
            return self.hc_tuples[-2][0].this_lsn
        except IndexError:
            return None

    @property
    def continue_left(self):
        return bool(self.hc_tuples[0][0].previous_lsn)

    @property
    def continue_right(self):
        return self.hc_tuples[-1][1].redo_operation != OperationCode.FORGET_TRANSACTION \
                    and self.hc_tuples[-1][1].undo_operation != OperationCode.COMPENSATION_LOG_RECORD

    @property
    def first_redo(self):
        return self.hc_tuples[0][1].deriv_redo_operation_type

    @property
    def first_undo(self):
        return self.hc_tuples[0][1].deriv_undo_operation_type

    @property
    def last_redo(self):
        return self.hc_tuples[-1][1].deriv_redo_operation_type

    @property
    def last_undo(self):
        return self.hc_tuples[-1][1].deriv_undo_operation_type

    @property
    def is_correct(self):
        return self.length > 1 and not self.continue_left and not self.continue_right

    @property
    def origin_pages(self):
        return [(h.page_nr, h.nr) for h, c in self.hc_tuples]

    @property
    def faulty_reasons(self):
        reasons = []
        if self.continue_left:
            reasons.append('need previous: ' + str(self.hc_tuples[0][0].previous_lsn))
        if self.continue_right:
            reasons.append('no forget+compensation')
        return reasons

    def format_string(self):
        return '%-10s %-20s Length: %-3s Prev: %-20s First: (%s, %s), Last: (%s, %s)' % (
            'Correct:  ' if self.is_correct else 'Incorrect:',
            str(self.mft_key) + ',',
            str(self.length) + ',',
            str(self.hc_tuples[0][0].previous_lsn),
            self.first_redo,
            self.first_undo,
            self.last_redo,
            self.last_undo)

    @property
    def contains_mft(self):
        return bool(sum(c.interpret_operation_data.operation_type == 'embedded mft' for _, c in self.hc_tuples))

    @property
    def contains_mft_attribute(self):
        return bool(sum(c.interpret_operation_data.operation_type == 'embedded mft attribute' for _, c in self.hc_tuples))

    @property
    def contains_usn(self):
        return bool(sum(c.interpret_operation_data.operation_type == 'embedded usn' for _, c in self.hc_tuples))

    @property
    def mft_references(self):
        return [(
            h.this_lsn,
            c.interpret_operation_data.operation_object.inum,
            c.interpret_operation_data.operation_object.sequence_value
                ) for h, c in self.hc_tuples if c.interpret_operation_data.operation_type == 'embedded mft']

    @property
    def mft_attributes(self):
        return [(
            h.this_lsn,
            c.interpret_operation_data.operation_object.enum.value
                ) for h, c in self.hc_tuples if c.interpret_operation_data.operation_type == 'embedded mft attribute']

    @property
    def usns(self):
        return [(
            h.this_lsn,
            c.interpret_operation_data.operation_object.usn
                ) for h, c in self.hc_tuples if c.interpret_operation_data.operation_type == 'embedded usn']

    @property
    def all_opcodes(self):
        return [(h.this_lsn, c.deriv_redo_operation_type, c.deriv_undo_operation_type) for h, c in self.hc_tuples]

    def attach_transaction_number_to_lsns(self):
        for h, _ in self.hc_tuples:
            h.transaction_num = self.transaction_num

    def format_output(self):
        return [
            self.mft_key,
            self.is_correct,
            self.length,
            self.transaction_num,
            ', '.join(['-'.join(tup) for tup in self.origin_pages]),
            self.hc_tuples[0][0].this_lsn,
            self.hc_tuples[-1][0].this_lsn,
            self.first_redo,
            self.first_undo,
            self.last_redo,
            self.last_undo,
            self.hc_tuples[0][0].previous_lsn or None,
            True if self.continue_right else None,
            str(self.mft_references)[1:-1],
            str(self.mft_attributes)[1:-1],
            str(self.usns)[1:-1],
            str(self.all_opcodes)[1:-1]
        ]