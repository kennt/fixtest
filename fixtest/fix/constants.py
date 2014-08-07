""" FIX protocol constants (message types)

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""


class FIX(object):
    """Provides constants for the FIX MsgType field (tag: 35)
    """

    # Some common field IDs
    MSGTYPE = 35
    CHECKSUM = 10

    # Some common Message Types
    HEARTBEAT = '0'
    TEST_REQUEST = '1'
    RESEND_REQUEST = '2'
    REJECT = '3'
    SEQUENCE_RESET = '4'
    LOGOUT = '5'
    IOI = '6'
    ADVERTISEMENT = '7'
    EXECUTION_REPORT = '8'
    ORDER_CANCEL_REQUEST = '9'
    LOGON = 'A'
    NEWORDER_SINGLE = 'D'

    _msgtype_map = {
        '0': 'Heartbeat',
        '1': 'TestRequest',
        '2': 'ResendRequest',
        '3': 'Reject',
        '4': 'SequenceReset',
        '5': 'Logout',
        '6': 'IOI',
        '7': 'Advertisement',
        '8': 'ExecutionReport',
        '9': 'OrderCancelReject',
        'AA': 'DerivativeSecurityList',
        'AB': 'NewOrderMultileg',
        'AC': 'MultilegOrderCancelReplace',
        'AD': 'TradeCaptureReportRequest',
        'AE': 'TradeCaptureReport',
        'AF': 'OrderMassStatusRequest',
        'AG': 'QuoteRequestReject',
        'AH': 'RFQRequest',
        'AI': 'QuoteStatusReport',
        'AJ': 'QuoteResponse',
        'AK': 'Confirmation',
        'AL': 'PositionMaintenanceRequest',
        'AM': 'PositionMaintenanceReport',
        'AN': 'RequestForPositions',
        'AO': 'RequestForPositionsAck',
        'AP': 'PositionReport',
        'AQ': 'TradeCaptureReportRequestAck',
        'AR': 'TradeCaptureReportAck',
        'AS': 'AllocationReport',
        'AT': 'AllocationReportAck',
        'AU': 'ConfirmationAck',
        'AV': 'SettlementInstructionRequest',
        'AW': 'AssignmentReport',
        'AX': 'CollateralRequest',
        'AY': 'CollateralAssignment',
        'AZ': 'CollateralResponse',
        'A': 'Logon',
        'BA': 'CollateralReport',
        'BB': 'CollateralInquiry',
        'BC': 'NetworkCounterpartySystemStatusRequest',
        'BD': 'NetworkCounterpartySystemStatusResponse',
        'BE': 'UserRequest',
        'BF': 'UserResponse',
        'BG': 'CollateralInquiryAck',
        'BH': 'ConfirmationRequest',
        'BI': 'TradingSessionListRequest',
        'BJ': 'TradingSessionList',
        'BK': 'SecurityListUpdateReport',
        'BL': 'AdjustedPositionReport',
        'BM': 'AllocationInstructionAlert',
        'BN': 'ExecutionAck',
        'BO': 'ContraryIntentionReport',
        'BP': 'SecurityDefinitionUpdateReport',
        'BQ': 'SettlementObligationReport',
        'BR': 'DerivativeSecurityListUpdateReport',
        'BS': 'TradingSessionListUpdateReport',
        'BT': 'MarketDefinitionRequest',
        'BU': 'MarketDefinition',
        'BV': 'MarketDefinitionUpdateReport',
        'BW': 'ApplicationMessageRequest',
        'BX': 'ApplicationMessageRequestAck',
        'BY': 'ApplicationMessageReport',
        'BZ': 'OrderMassActionReport',
        'B': 'News',
        'CA': 'OrderMassActionRequest',
        'CB': 'UserNotification',
        'CC': 'StreamAssignmentRequest',
        'CD': 'StreamAssignmentReport',
        'CE': 'StreamAssignmentReportACK',
        'CF': 'PartyDetailsListRequest',
        'CG': 'PartyDetailsListReport',
        'CH': 'MarginRequirementInquiry',
        'CI': 'MarginRequirementInquiryAck',
        'CJ': 'MarginRequirementReport',
        'CK': 'PartyDetailsListUpdateReport',
        'CL': 'PartyRiskLimitsRequest',
        'CM': 'PartyRiskLimitsReport',
        'CN': 'SecurityMassStatusRequest',
        'CO': 'SecurityMassStatus',
        'CQ': 'AccountSummaryReport',
        'CR': 'PartyRiskLimitsUpdateReport',
        'CS': 'PartyRiskLimitsDefinitionRequest',
        'CT': 'PartyRiskLimitsDefinitionRequestAck',
        'CU': 'PartyEntitlementsRequest',
        'CV': 'PartyEntitlementsReport',
        'CW': 'QuoteAck',
        'CX': 'PartyDetailsDefinitionRequest',
        'CY': 'PartyDetailsDefinitionRequestAck',
        'CZ': 'PartyEntitlementsUpdateReport',
        'C': 'Email',
        'DA': 'PartyEntitlementsDefinitionRequest',
        'DB': 'PartyEntitlementsDefinitionRequestAck',
        'DC': 'TradeMatchReport',
        'DD': 'TradeMatchReportAck',
        'D': 'NewOrderSingle',
        'E': 'NewOrderList',
        'F': 'OrderCancelRequest',
        'G': 'OrderCancelReplaceRequest',
        'H': 'OrderStatusRequest',
        'J': 'AllocationInstruction',
        'K': 'ListCancelRequest',
        'L': 'ListExecute',
        'M': 'ListStatusRequest',
        'N': 'ListStatus',
        'P': 'AllocationInstructionAck',
        'Q': 'DontKnowTrade',
        'R': 'QuoteRequest',
        'S': 'Quote',
        'T': 'SettlementInstructions',
        'V': 'MarketDataRequest',
        'W': 'MarketDataSnapshotFullRefresh',
        'X': 'MarketDataIncrementalRefresh',
        'Y': 'MarketDataRequestReject',
        'Z': 'QuoteCancel',
        'a': 'QuoteStatusRequest',
        'b': 'MassQuoteAck',
        # 'b': 'MassQuoteAcknowledgement',
        'c': 'SecurityDefinitionRequest',
        'd': 'SecurityDefinition',
        'e': 'SecurityStatusRequest',
        'f': 'SecurityStatus',
        'g': 'TradingSessionStatusRequest',
        'h': 'TradingSessionStatus',
        'i': 'MassQuote',
        'j': 'BusinessMessageReject',
        'k': 'BidRequest',
        'l': 'BidResponse',
        'm': 'ListStrikePrice',
        'n': 'XMLnonFIX',
        'o': 'RegistrationInstructions',
        'p': 'RegistrationInstructionsResponse',
        'q': 'OrderMassCancelRequest',
        'r': 'OrderMassCancelReport',
        's': 'NewOrderCross',
        't': 'CrossOrderCancelReplaceRequest',
        'u': 'CrossOrderCancelRequest',
        'v': 'SecurityTypeRequest',
        'w': 'SecurityTypes',
        'x': 'SecurityListRequest',
        'y': 'SecurityList',
        'z': 'DerivativeSecurityListRequest ',
    }

    _exectype_map = {
        '0': 'New',
        '1': 'PartialFill',
        '2': 'Fill',
        '3': 'DoneForDay',
        '4': 'Canceled',
        '5': 'Replaced',
        '6': 'PendingCancel',
        '7': 'Stopped',
        '8': 'Rejected',
        '9': 'Suspended',
        'A': 'PendingNew',
        'B': 'Calculated',
        'C': 'Expired',
        'D': 'Restated',
        'E': 'PendingReplace',
        'F': 'Trade',
        'G': 'TradeCorrect',
        'H': 'TradeCancel',
        'I': 'OrderStatus',
        'J': 'TradeInAClearingHold',
        'K': 'TradeHasBeenReleasedToClearing',
        'L': 'TriggeredOrActivatedBySystem',
        'M': 'Locked',
        'N': 'Released',
    }

    @staticmethod
    def find_msgtype(key):
        """ Maps the message type constant used in the protocol
            to a descriptive string.

        Args:
            key: A string that is a value (in the FIX protocol).

        Returns:
            Returns a string that contains the more descriptive string.
            If the value does not exist, '???' is returned.
        """
        return FIX._msgtype_map.get(str(key), '???')

    @staticmethod
    def find_exectype(key):
        """ Maps the exec type constant used in the protocol
            to a descriptive string.

        Args:
            key: A string that is a value (in the FIX protocol).

        Returns:
            Returns a string that contains the more descriptive string.
            If the value does not exist, '???' is returned.
        """
        return FIX._exectype_map.get(str(key), '???')
