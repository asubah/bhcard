#! /usr/bin/env python
from smartcard.System import readers
from smartcard.Exceptions import NoCardException

class BhCard:
    """ Get the data from the card """
    @staticmethod
    def sendCommand(SELECT, connection):
        data, sw1, sw2 = connection.transmit(SELECT)
        if (sw1 != 0x09):
            return data
        else:
            print ("Error: can't read!")
            return None

    @staticmethod
    def getData():
        card_data = {}

        # get all the available readers
        r = readers()
        
        if len(r) == 0:
            print("Error: No readers available!")
            return None

        print("Available readers:", r)
        
        reader = r[0]
        print("Using:", reader)
        
        connection = reader.createConnection()

        try:
            connection.connect()
        except NoCardException:
            print("Error: No card found!")
            return None

        # Select DF by name
        SELECT = [0x00,0xA4,0x04,0x00,0x0D,0xD4,0x99,0x00,0x00,0x01,0x01,0x01,0x00,0x01,0x00,0x00,0x00,0x01]
        BhCard.sendCommand(SELECT, connection)

        # Select DF file
        SELECT = [0x00,0xA4,0x00,0x0C,0x02,0x01,0x01]
        BhCard.sendCommand(SELECT, connection)
        
        # Select 1st data file
        SELECT = [0x00,0xA4,0x02,0x0C,0x02,0x00,0x01]
        BhCard.sendCommand(SELECT, connection)
        
        # Read 1st Record of data file
        SELECT = [0x00,0xB0,0x00,0x00,0xFF]
        data = BhCard.sendCommand(SELECT, connection)

        if data:
            # CPR
            card_data['cpr'] = ''.join([chr(c) for c in data[0:9]])

            # NAME
            full_name = ''
            for i in range(1, 7):
                name_start = 9 + (32 * (i-1))
                name_end = 9 + (32 * i)
                name_key = 'name' + str(i)
                name = data[name_start: name_end]
                name = ''.join([chr(c) for c in name])
                name = ''.join(name.split(' '))
                card_data[name_key] = name
                full_name = (full_name + ' ' + name).strip()

            card_data['full_name'] = full_name.strip()
        
        # Select 2nd data file
        SELECT = [0x00,0xA4,0x02,0x0C,0x02,0x00,0x02]
        BhCard.sendCommand(SELECT, connection)
        
        # Read Record of 2nd data file
        SELECT = [0x00,0xB0,0x00,0x00,0x24]
        data = BhCard.sendCommand(SELECT, connection)

        if data:
            # ISSUE DATE
            tmp_str = ''.join([chr(c) for c in data[8:16]])
            card_data['issue_date'] = tmp_str[0:4] + '-' + tmp_str[4:6] + '-' + tmp_str[6:8]

            # EXPIRY DATE
            tmp_str = ''.join([chr(c) for c in data[0:8]])
            card_data['expiry_date'] = tmp_str[0:4] + '-' + tmp_str[4:6] + '-' + tmp_str[6:8]
        
        # Select 3rd data file
        SELECT = [0x00,0xA4,0x02,0x0C,0x02,0x00,0x06]
        BhCard.sendCommand(SELECT, connection)
        
        # Select 3rd data file
        SELECT = [0x00,0xB0,0x00,0x00,0xFF]
        data = BhCard.sendCommand(SELECT, connection)

        if data:
            # WORKPLACE
            workplace = ''.join([chr(x) for x in data][201:]).strip()
            card_data['workplace'] = workplace

        return card_data
