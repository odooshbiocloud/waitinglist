from odoo.tests.common import TransactionCase


class TestWaitingList(TransactionCase):

    def setUp(self):
        super(TestWaitingList, self).setUp()
        self.WaitingList = self.env['waiting.list']
        self.Partner = self.env['res.partner']
        
        # Create a test partner
        self.test_partner = self.Partner.create({
            'name': 'Test Customer',
            'phone': '+123456789',
        })

    def test_create_waiting_list_entry(self):
        """Test creating a waiting list entry"""
        entry = self.WaitingList.create({
            'partner_id': self.test_partner.id,
            'party_size': 4,
            'estimated_wait_time': 15,
            'notes': 'Test entry',
        })
        
        self.assertEqual(entry.state, 'waiting')
        self.assertEqual(entry.party_size, 4)
        self.assertEqual(entry.partner_id.id, self.test_partner.id)
        self.assertTrue(entry.name)  # Should have auto-generated name

    def test_seat_customer(self):
        """Test seating a customer"""
        entry = self.WaitingList.create({
            'partner_id': self.test_partner.id,
            'party_size': 2,
        })
        
        entry.action_seat()
        self.assertEqual(entry.state, 'seated')
        self.assertTrue(entry.seated_time)

    def test_cancel_entry(self):
        """Test canceling an entry"""
        entry = self.WaitingList.create({
            'partner_id': self.test_partner.id,
            'party_size': 3,
        })
        
        entry.action_cancel()
        self.assertEqual(entry.state, 'cancelled')

    def test_no_show_entry(self):
        """Test marking entry as no-show"""
        entry = self.WaitingList.create({
            'partner_id': self.test_partner.id,
            'party_size': 2,
        })
        
        entry.action_no_show()
        self.assertEqual(entry.state, 'no_show')