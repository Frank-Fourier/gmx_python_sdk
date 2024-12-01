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
        Get the available markets from the reader contract and optionally filter by specific addresses

        Returns
        -------
        Markets: tuple
            tuple of raw output from the reader contract, filtered if target_markets provided.

        """
        reader_contract = get_reader_contract(self.chain)
        data_store_contract_address = (
            contract_map[self.chain]['datastore']['contract_address']
        )
        
        raw_markets = reader_contract.functions.getMarkets(
            data_store_contract_address,
            0,
            1000
        ).call()
        
        target_markets = [
            "0x7f1fa204bb700853D36994DA19F830b6Ad18455C",
            "0x09400D9DB990D5ed3f35D7be61DfAEB900Af03C9",
            "0x2b477989A149B17073D9C9C82eC9cB03591e20c6",
            "0x47c031236e19d024b42f8AE6780E44A573170703"
        ]
        
        if target_markets:
            # Convert to lowercase for case-insensitive comparison
            target_markets = [addr.lower() for addr in target_markets]
            raw_markets = [
                market for market in raw_markets 
                if market[0].lower() in target_markets
            ]
        
        print("\nFiltered Markets from GMX Contract:")
        for market in raw_markets:
            print(f"""
Market Details:
- Market Address: {market[0]}
- Index Token: {market[1]}
- Long Token: {market[2]}
- Short Token: {market[3]}
""")
        
        return raw_markets

    def _process_markets(self):
        """
        Call and process the raw market data

        Returns
        -------
        decoded_markets : dict
            dictionary of decoded market data.

        """
        token_address_dict = get_tokens_address_dict(self.chain)
        raw_markets = self._get_available_markets_raw()

        decoded_markets = {}
        for raw_market in raw_markets:
            try:

                if not self._check_if_index_token_in_signed_prices_api(raw_market[1]):
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
                if not self._check_if_index_token_in_signed_prices_api(raw_market[1]):
                    continue
                decoded_markets[raw_market[0]] = {
                    'gmx_market_address': raw_market[0],
                    'market_symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    ),
                    'index_token_address': raw_market[1],
                    'market_metadata': {'symbol': 'SWAP {}-{}'.format(
                        token_address_dict[raw_market[2]]['symbol'],
                        token_address_dict[raw_market[3]]['symbol']
                    )},
                    'long_token_metadata': token_address_dict[raw_market[2]],
                    'long_token_address': raw_market[2],
                    'short_token_metadata': token_address_dict[raw_market[3]],
                    'short_token_address': raw_market[3]
                }

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
