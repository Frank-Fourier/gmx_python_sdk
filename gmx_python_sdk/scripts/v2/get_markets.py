from .gmx_utils import (
    contract_map, get_tokens_address_dict, get_reader_contract
)

from .get_oracle_prices import GetOraclePrices


class GetMarkets:
    def __init__(self, chain):
        self.chain = chain

    def get_available_markets(self):
        """
        Get the available markets on a given chain

        Returns
        -------
        Markets: dict
            dictionary of the available markets.

        """
        return self._process_markets()

    def _get_available_markets_raw(self):
        """
        Get the available markets from the reader contract

        Returns
        -------
        Markets: tuple
            tuple of raw output from the reader contract.

        """
        reader_contract = get_reader_contract(self.chain)
        data_store_contract_address = (
            contract_map[self.chain]['datastore']['contract_address']
        )

        return reader_contract.functions.getMarkets(
            data_store_contract_address,
            0,
            17
        ).call()

    def _process_markets(self):
        """
        Call and process the raw market data

        Returns
        -------
        decoded_markets : dict
            dictionary decoded market data.

        """
        token_address_dict = get_tokens_address_dict(self.chain)
        raw_markets = self._get_available_markets_raw()
        
        print(f"\nTotal markets found in contract: {len(raw_markets)}")
        
        decoded_markets = {}
        filtered_out_markets = []
        
        for raw_market in raw_markets:
            try:
                if not self._check_if_index_token_in_signed_prices_api(raw_market[1]):
                    filtered_out_markets.append({
                        'market_address': raw_market[0],
                        'index_token': raw_market[1],
                        'reason': 'Not in signed prices API'
                    })
                    continue
                
                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': (
                        token_address_dict[raw_market[1]]['symbol']
                    ),
                    'index_token_address': raw_market[1],
                    'market_metadata': token_address_dict[raw_market[1]],
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }

            # If KeyError it is because there is no market symbol and it is a
            # swap market
            except KeyError:
                filtered_out_markets.append({
                    'market_address': raw_market[0],
                    'index_token': raw_market[1],
                    'reason': 'KeyError during processing'
                })
                continue
        
        print(f"\nProcessed markets: {len(decoded_markets)}")
        print(f"Filtered out markets: {len(filtered_out_markets)}")
        print("\nFiltered out market details:")
        for market in filtered_out_markets:
            print(f"- Market {market['market_address']}: {market['reason']}")
        
        return decoded_markets

    def _check_if_index_token_in_signed_prices_api(self, index_token_address):

        try:
            prices = GetOraclePrices(chain=self.chain).get_recent_prices()

            if index_token_address == "0x0000000000000000000000000000000000000000":
                return True
            prices[index_token_address]
            return True
        except KeyError:

            print("{} market not live on GMX yet..".format(index_token_address))
            return False


if __name__ == '__main__':
    raw_markets = GetMarkets(
        chain="arbitrum"
    ).get_available_markets(clean=False)
