# Binance Reconciliation Guide

Version Log

| **Version** | **Date** | **Author** | **Summary** |
| --- | --- | --- | --- |
| v0.1 | 2025-07-25 | CW | 1st draft for spot wallet |
|  |  |  |  |

This guide provide a detailed requirements of how the Python Script should work and what are the target outcomes (i.e. Rule-based classification process)

For Users who have Binance account(s), we should have obtained the read-only API keys from the onboarding process. After that, the scripts should build the following table according to this guide.

# Structure

Binance Rest API → `binance_client.py` → Raw Data DB →  `binance_canoical.py` → Reconciliation DB → `match_aggregate.py` → pre-final Transaction DB → frontend user manual process updates → final Transaction DB

# Data Schema

## Raw Binance DB

All data obtained from Binance will store in tables under the Raw Binance DB.

We confirm no missing and no duplication of this DB since `start_date` (obtained from onboarding process). However, some Binance endpoint cannot obtain historical data, especially for snapshot data.

## Reconciliation DB

The following tables are required for spot wallet under this DB:

- Transfer DB
    | **Field** | **Description** |
    | --- | --- |
    | pid | Primary key |
    | source | source table name |
    | fid | Foreign key to the source table |
    | external_id | ID to the original source |
    | datetime | Defined by functions below, sourced from Raw Binance DB |
    | txn_type | Defined by functions below (transfer_in, transfer_out, txn_fee) |
    | txn_subtype | Defined by functions below (deposit, transfer_between_accounts, transfer_between_wallets, withdrawal_fee) |
    | email | Account Email. Defined by or mapped from function input parameter |
    | wallet | SPOT, MARGIN, FUTURE |
    | asset | Copy from Raw Binance DB |
    | amount | Copy from Raw Binance DB |
    | counterParty | Copy from Raw Binance DB |
    | network | Copy from Raw Binance DB |
    | txn_hash | Copy from Raw Binance DB |
    | match_id | Defined by match engine |
    | reconciled | true or false, resulted from reconcile functions |

- Trade DB    
    | **Field** | **Description** |
    | --- | --- |
    | pid | Primary key |
    | source | source table name |
    | fid | Foreign key to the source table |
    | external_id | ID to the original source |
    | datetime | Defined by functions below, sourced from Raw Binance DB |
    | txn_type | Defined by functions below (trade) |
    | txn_subtype | Defined by functions below (spot_buy, spot_sell, maker_fee, taker_fee) |
    | email | Account Email. Defined by or mapped from function input parameter |
    | wallet | SPOT |
    | symbol | Copy from Raw Binance DB |
    | asset | Copy from Raw Binance DB |
    | amount | Copy from Raw Binance DB |
    | agg_id | Defined by smart aggregator engine |
    | reconciled | true or false, resulted from reconcile functions |


- Balance DB    
    | **Field** | **Description** |
    | --- | --- |
    | pid | Primary key |
    | source | source table name |
    | fid | Foreign key to the source table |
    | external_id | ID to the original source |
    | date | Date of the balances |
    | email | Account Email. Defined by or mapped from function input parameter |
    | wallet | SPOT, MARGIN, FUTURE |
    | asset | Copy from Raw Binance DB |
    | raw_balance | Binance raw balance. Defined by functions below |
    | raw_loan | Binance raw balance. Defined by functions below |
    | raw_interest | Binance raw balance. Defined by functions below |
    | raw_unrealisedPnL | Binance raw balance. Defined by functions below |
    | cal_balance | calculated balance. Defined by functions below |
    | cal_loan | calculated balance. Defined by functions below |
    | cal_interest | calculated balance. Defined by functions below |
    | cal_unrealisedPnL | calculated balance. Defined by functions below |
    | variance_inAsset | Varied amount in original asset |
    | variance_inUSD | Varied amount in USD |

(This guide will update for other wallet types later)

# Required functions

function `get_daily_snapshot(api_key, startTime, endTime)`:

- For each `account` type (”main account”, “sub account”)
- For each `wallet` type (”SPOT”,  “MARGIN”, “FUTURES”)
- Get `/sapi/v1/accountSnapshot`
- Store the raw response into `cex.binance.raw.daily_snapshot`
- Standardise the raw data to `cex.binance.processed.balances` as per below:
    - For type=SPOT:
        - Example Request
            
            ```json
            import requests
            
            url = "{{url}}/sapi/v1/accountSnapshot?type=SPOT&timestamp=&signature="
            
            payload = {}
            headers = {
              'X-MBX-APIKEY': '',
              'Accept': 'application/json'
            }
            
            response = requests.request("GET", url, headers=headers, data=payload)
            
            print(response.text)
            ```
            
        - Example Response
            
            ```json
            {
                "code": 200,
                "msg": "",
                "snapshotVos": [
                    {
                        "type": "spot",
                        "updateTime": 1752969599000,
                        "data": {
                            "totalAssetOfBtc": "0.00000897",
                            "balances": [
                                {
                                    "asset": "BNB",
                                    "free": "0.00094858",
                                    "locked": "0"
                                },
                                {
                                    "asset": "USDC",
                                    "free": "0.27725",
                                    "locked": "0"
                                },
                                {
                                    "asset": "USDT",
                                    "free": "0.0851",
                                    "locked": "0"
                                }
                            ]
                        }
                    },
            ```
            
        - Create records to `cex.binance.processed.balances`
            - source = `cex.binance.raw.daily_snapshot`
            - date = `updateTime`
            - email = mapped from query api key
            - wallet = “SPOT”
                - asset = `asset`
            - raw_balance = `free` + `locked`
    - For type=FUTURES:
        - Example Request
            
            ```json
            import requests
            
            url = "{{url}}/sapi/v1/accountSnapshot?type=FUTURES&timestamp=&signature="
            
            payload = {}
            headers = {
              'X-MBX-APIKEY': '',
              'Accept': 'application/json'
            }
            
            response = requests.request("GET", url, headers=headers, data=payload)
            
            print(response.text)
            ```
            
        - Example Response
            
            ```json
            {
                "code": 200,
                "msg": "",
                "snapshotVos": [
                    {
                        "type": "futures",
                        "updateTime": 1752969599000,
                        "data": {
                            "assets": [
                                {
                                    "asset": "USDT",
                                    "marginBalance": "53.39282143",
                                    "walletBalance": "53.26344143"
                                }
                            ],
                            "position": [
                                {
                                    "symbol": "ETHUSDT",
                                    "entryPrice": "0",
                                    "markPrice": "3591.31",
                                    "positionAmt": "0",
                                    "unRealizedProfit": "0"
                                },
                                {
                                    "symbol": "BNBUSDT",
                                    "entryPrice": "0",
                                    "markPrice": "733.43",
                                    "positionAmt": "0",
                                    "unRealizedProfit": "0"
                                },
                                {
                                    "symbol": "AIOTUSDT",
                                    "entryPrice": "0",
                                    "markPrice": "0.32322808",
                                    "positionAmt": "0",
                                    "unRealizedProfit": "0"
                                },
                                {
                                    "symbol": "CUSDT",
                                    "entryPrice": "0.4986731",
                                    "markPrice": "0.26416102",
                                    "positionAmt": "200",
                                    "unRealizedProfit": "0.12938"
                                }
                            ]
                        }
                    },
            ```
            
        - Create records to `cex.binance.processed.balances`
            - source = `cex.binance.raw.daily_snapshot`
            - date = `updateTime`
            - email = mapped from query api key
            - wallet = “FUTURES”
            - asset = `asset`
            - raw_balance = `walletBalance`
            - raw_unrealisedPnL = sum(`unRealizedProfit`)
    - For type=MARGIN:
        - Example Request
            
            ```json
            import requests
            
            url = "{{url}}/sapi/v1/accountSnapshot?type=MARGIN&timestamp=&signature="
            
            payload = {}
            headers = {
              'X-MBX-APIKEY': '',
              'Accept': 'application/json'
            }
            
            response = requests.request("GET", url, headers=headers, data=payload)
            
            print(response.text)
            ```
            
        - Example Response
            
            ```json
            {
                "code": 200,
                "msg": "",
                "snapshotVos": [
                    {
                        "type": "margin",
                        "updateTime": 1752969599000,
                        "data": {
                            "marginLevel": "1.56724195",
                            "totalAssetOfBtc": "0.00051876",
                            "totalLiabilityOfBtc": "0.000331",
                            "totalNetAssetOfBtc": "0.00016938",
                            "userAssets": [
                                {
                                    "asset": "1000CAT",
                                    "borrowed": "4361.3",
                                    "free": "4357.0386",
                                    "interest": "5.96057751",
                                    "locked": "0",
                                    "netAsset": "-10.22197751"
                                },
                                {
                                    "asset": "USDT",
                                    "borrowed": "0",
                                    "free": "20.0464071",
                                    "interest": "0",
                                    "locked": "0",
                                    "netAsset": "20.0464071"
                                }
                            ]
                        }
                    },
            ```
            
        - Create records to `cex.binance.processed.balances`
            - source = `cex.binance.raw.daily_snapshot`
            - date = `updateTime`
            - email = mapped from query api key
            - wallet = “MARGIN”
            - asset = `asset`
            - raw_balance = `locked` + `free`
            - raw_loan = `borrowed` *-1
            - raw_interest = `interest` *-1

---

function `get_deposit_history(api_key, startTime, endTime)`:

- For each `account` type (”main account”, “sub account”)
- Get `/sapi/v1/capital/deposit/hisrec`
- Store the raw response into `cex.binance.raw.deposit_history`
- Standardise the raw data to `cex.binance.processed.transfers` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/sapi/v1/capital/deposit/hisrec?timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```python
        [
            {
                "id": "4599842267854362625",
                "amount": "20.01",
                "coin": "USDC",
                "network": "BASE",
                "status": 1,
                "address": "0x120cd09864d315f2d3b25b99641095eb205c630e",
                "addressTag": "",
                "txId": "0xa796928dd5ffaaf1dc25e8c8312ba319186ace067f3e7015b7866cfd71a6b523",
                "insertTime": 1752130364000,
                "completeTime": 1752131289000,
                "transferType": 0,
                "confirmTimes": "2/1",
                "unlockConfirm": 2,
                "walletType": 0
            },
        ```
        
    - Create records for each account to `cex.binance.processed.transfers`  as per below:
        - source = `cex.binance.raw.deposit_history`
        - external_id = id
        - datetime = insertTime
        - txn_type = “transfer_in”
        - txn_subtype = “deposit”
        - email = mapped from query api key
        - wallet = “SPOT”
        - asset = coin
        - amount = amount
        - counterParty = address
        - network = network
        - txn_hash = txId

---

function `get_withdraw_history(api_key, startTime, endTime)`:

- For main `account` type
- Get `/sapi/v1/capital/withdraw/history`
- Store the raw response into `cex.binance.raw.withdraw_history`
- Standardise the raw data to `cex.binance.processed.transfers` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/sapi/v1/capital/withdraw/history?timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```python
        [
            {
                "id": "c2f76cde5911491d83390320eb793071",
                "amount": "251.71",
                "transactionFee": "0.3",
                "coin": "USDC",
                "status": 6,
                "address": "0x8F35E070F4b57E16322A1f12266BDE5ecd4e9f83",
                "txId": "0xd9f0eb8ecf472a4c8cc37019e9ead7d9d348f9cf533c987cd2128a764a303b95",
                "applyTime": "2025-07-21 06:25:32", // UTC
                "network": "BASE",
                "transferType": 0,
                "info": "0x3304e22ddaa22bcdc5fca2269b418046ae7b566a,4124318",
                "confirmNo": 1,
                "walletType": 0,
                "txKey": "",
                "completeTime": "2025-07-21 06:26:07"
            },
            {
                "id": "7cba207e7dfb430d933bebdb3bc1addc",
                "amount": "0.44261",
                "transactionFee": "0.00005",
                "coin": "ETH",
                "status": 6,
                "address": "0x54a57cd9f7e5d97c4dc378c60f2a804689885016",
                "txId": "0x3c54a59bd482ca9d88f299bec1374eaec5c4f99ae2bae8b5af5f8bd95d58a25e",
                "applyTime": "2025-05-18 12:49:13",
                "network": "BASE",
                "transferType": 0,
                "info": "0x3304e22ddaa22bcdc5fca2269b418046ae7b566a,3745574",
                "confirmNo": 1,
                "walletType": 0,
                "txKey": "",
                "completeTime": "2025-05-18 12:50:10"
            }
        ]
        ```
        
    - Create 1 withdraw record and 1 fee record where status = 6 (Completed) for each withdraw to `cex.binance.processed.transfers`  as per below:
        - withdraw record
            - source = `cex.binance.raw.withdraw_history`
            - external_id = id
            - datetime = completeTime
            - txn_type = “transfer_out”
            - txn_subtype = “withdraw”
            - email = mapped from query api key
            - wallet = “SPOT”
            - asset = coin
            - amount = amount * -1
            - counterParty = address
            - network = network
            - txn_hash = txId
        - fee record
            - source = source = `cex.binance.raw.withdraw_history`
            - external_id = id
            - datetime = completeTime
            - txn_type = “txn_fee”
            - txn_subtype = “withdrawal_fee”
            - email = mapped from query api key
            - wallet = “SPOT”
            - asset = coin
            - amount = transactionFee * -1
            - counterParty = address
            - network = network
            - txn_hash = txId

---

function `get_transfer_between_account_main_spot(api_key, startTime, endTime)`:

- For each `account` type = ”main account”
- For each `wallet` type = ”SPOT”
- Get `/sapi/v1/sub-account/sub/transfer/history`
- Store the raw response into `cex.binance.raw.transfer_between_account_main_spot`
- Standardise the raw data to `cex.binance.processed.transfers` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/sapi/v1/sub-account/sub/transfer/history?timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```python
        [
            {
                "from": "ken@kenhung.io",
                "to": "cameron.w@prodds.xyz",
                "asset": "USDT",
                "qty": "1.02000000",
                "time": 1753500940000,
                "status": "SUCCESS",
                "tranId": 279592812928
            },
        ```
        
    - Create 1 record for “main account” and 1 record for “sub account” to `cex.binance.processed.transfers`
    - For “main account”
        - source = `cex.binance.raw.transfer_between_account_main_spot`
        - external_id = tranId
        - datetime = time
        - txn_type = “transfer_in” if to == email, “transfer_out” if from == email
        - txn_subtype = “transfer_between_account_main_spot”
        - email = mapped from query api key
        - wallet = “SPOT”
        - asset = `asset`
        - amount = qty if txn_type == transfer_in, txn_type = transfer_out == qty * -1
        - counterParty = to if txn_type == transfer_out, from if txn_type = transfer_in
        - raw_interest = `interest` *-1
    - For “sub account”
        - source = `cex.binance.raw.transfer_between_account_main_spot`
        - external_id = tranId
        - datetime = time
        - txn_type = if “main account” record is a “transfer_in”, then it is a “transfer_out”, else “transfer_in”
        - txn_subtype = “transfer_between_account_main_spot”
        - email = if txn_type = “transfer_in”, to, else from
        - wallet = “SPOT”
        - asset = `asset`
        - amount = qty if txn_type == transfer_in, txn_type = transfer_out == qty * -1
        - counterParty = to if txn_type == transfer_out, from if txn_type = transfer_in
        - raw_interest = `interest` *-1

---

function `get_transfer_between_account_sub(api_key, startTime, endTime)`:

- For each `account` type = ”sub account”
- Get `/sapi/v1/sub-account/transfer/subUserHistory`
- Store the raw response into `cex.binance.raw.transfer_between_account_sub`
- Standardise the raw data to `cex.binance.processed.transfers` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/sapi/v1/sub-account/transfer/subUserHistory?timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```python
        [
            {
                "counterParty": "master",
                "email": "ken@kenhung.io",
                "type": 2,
                "asset": "USDT",
                "qty": "1.40000000",
                "time": 1753500828000,
                "status": "SUCCESS",
                "tranId": 279592422281,
                "fromAccountType": "SPOT",
                "toAccountType": "SPOT"
            },
        ```
        
    - Create 1 record for “main account” and 1 record for “sub account” to `cex.binance.processed.transfers`
    - For “sub account”
        - source = `cex.binance.raw.transfer_between_account_sub`
        - external_id = tranId
        - datetime = time
        - txn_type = “transfer_in” if type == 1, “transfer_out” if type == 2
        - txn_subtype = “transfer_between_account_sub”
        - email = mapped from query api key
        - wallet = toAccountType if type == 1, fromAccountType if type == 2
        - asset = `asset`
        - amount = qty if txn_type == transfer_in, txn_type = transfer_out == qty * -1
        - counterParty = email (from API response)
    - For “main account”
        - source = `cex.binance.raw.transfer_between_account_sub`
        - external_id = tranId
        - datetime = time
        - txn_type = “transfer_out” if type = 1, “transfer_in” if type = 2
        - txn_subtype = “transfer_between_account_main_spot”
        - email = email (from API response)
        - wallet = toAccountType if type == 2, fromAccountType if type == 1
        - asset = `asset`
        - amount = qty if txn_type == transfer_in, txn_type = transfer_out == qty * -1
        - counterParty = mapped from query api key

---

function `get_transfer_between_wallets(api_key, type, startTime, endTime)`:

- For each `account` type (”main account”, “sub account”)
- Get `/sapi/v1/asset/transfer`
- type is a required field for this API, which is joined fromWallet with toWallet using “_”, e.g. MAIN_UMFUTURE, refers to Spot account transfer to USDⓈ-M Futures account.
- ENUM of transfer types:
    - MAIN_UMFUTURE Spot account transfer to USDⓈ-M Futures account
    - MAIN_CMFUTURE Spot account transfer to COIN-M Futures account
    - MAIN_MARGIN Spot account transfer to Margin（cross）account
    - UMFUTURE_MAIN USDⓈ-M Futures account transfer to Spot account
    - UMFUTURE_MARGIN USDⓈ-M Futures account transfer to Margin（cross）account
    - CMFUTURE_MAIN COIN-M Futures account transfer to Spot account
    - CMFUTURE_MARGIN COIN-M Futures account transfer to Margin(cross) account
    - MARGIN_MAIN Margin（cross）account transfer to Spot account
    - MARGIN_UMFUTURE Margin（cross）account transfer to USDⓈ-M Futures
    - MARGIN_CMFUTURE Margin（cross）account transfer to COIN-M Futures
    - ~~ISOLATEDMARGIN_MARGIN Isolated margin account transfer to Margin(cross) account [Out of Scope]~~
    - ~~MARGIN_ISOLATEDMARGIN Margin(cross) account transfer to Isolated margin account [Out of Scope]~~
    - ~~ISOLATEDMARGIN_ISOLATEDMARGIN Isolated margin account transfer to Isolated margin account [Out of Scope]~~
    - ~~MAIN_FUNDING Spot account transfer to Funding account [Out of Scope]~~
    - ~~FUNDING_MAIN Funding account transfer to Spot account [Out of Scope]~~
    - ~~FUNDING_UMFUTURE Funding account transfer to UMFUTURE account [Out of Scope]~~
    - ~~UMFUTURE_FUNDING UMFUTURE account transfer to Funding account [Out of Scope]~~
    - ~~MARGIN_FUNDING MARGIN account transfer to Funding account [Out of Scope]~~
    - ~~FUNDING_MARGIN Funding account transfer to Margin account [Out of Scope]~~
    - ~~FUNDING_CMFUTURE Funding account transfer to CMFUTURE account [Out of Scope]~~
    - ~~CMFUTURE_FUNDING CMFUTURE account transfer to Funding account [Out of Scope]~~
    - MAIN_OPTION Spot account transfer to Options account
    - OPTION_MAIN Options account transfer to Spot account
    - UMFUTURE_OPTION USDⓈ-M Futures account transfer to Options account
    - OPTION_UMFUTURE Options account transfer to USDⓈ-M Futures account
    - MARGIN_OPTION Margin（cross）account transfer to Options account
    - OPTION_MARGIN Options account transfer to Margin（cross）account
    - ~~FUNDING_OPTION Funding account transfer to Options account [Out of Scope]~~
    - ~~OPTION_FUNDING Options account transfer to Funding account [Out of Scope]~~
    - ~~MAIN_PORTFOLIO_MARGIN Spot account transfer to Portfolio Margin account [Out of Scope]~~
    - ~~PORTFOLIO_MARGIN_MAIN Portfolio Margin account transfer to Spot account [Out of Scope]~~
- Store the raw response into `cex.binance.raw.transfer_between_wallets`
- Standardise the raw data to `cex.binance.processed.transfers` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/sapi/v1/asset/transfer?type=MAIN_UMFUTURE&timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```json
        {
            "total": 1,
            "rows": [
                {
                    "timestamp": 1753518333000,
                    "asset": "USDT",
                    "amount": "23.3341376",
                    "type": "MAIN_UMFUTURE",
                    "status": "CONFIRMED",
                    "tranId": 279647787183
                }
            ]
        }
        ```
        
    - Create 1 records for fromWallet and 1 record toWallet” for each account (both main and sub) to `cex.binance.processed.transfers`
        - source = `cex.binance.raw.transfer_between_wallets`
        - external_id = tranId
        - datetime = timestamp
        - txn_type = “transfer_in” or “transfer_out”
        - txn_subtype = “transfer_between_wallets”
        - email = mapped from query api key
        - wallet = mapped from query type (limited to 4 types only for now, “SPOT”, “FUTURES”, “MARGIN”, “OPTION”)
            - SPOT includes both “SPOT” and “FUNDING”
            - FUTURES includes both “UMFUTURE” and “CMFUTURE”
            - MARGIN includes both “MARGIN” and “ISOLATEDMARGIN”
        - asset = asset
        - amount = amount if txn_type = transfer_in, amount * -1 if txn_type = transfer_out
        - counterParty = NaN (Not applicable as this refer to transfer within the same account)

---

function `get_trades(api_key, startTime, endTime, quoteAsset, baseAsset)`:

- For each `account` type (”main account”, “sub account”)
- For `wallet` type = spot
- Get `/api/v3/myTrades`
- Store the raw response into `cex.binance.raw.trades`
- Standardise the raw data to `cex.binance.processed.trades` as per below:
    - Example Request
        
        ```python
        import requests
        
        url = "{{url}}/api/v3/myTrades?symbol=DOGEUSDC&timestamp=&signature="
        
        payload = {}
        headers = {
          'X-MBX-APIKEY': '',
          'Accept': 'application/json'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        
        print(response.text)
        ```
        
    - Example Response
        
        ```python
        [
            {
                "symbol": "DOGEUSDC",
                "id": 26739262,
                "orderId": 1291553393,
                "orderListId": -1,
                "price": "0.18202000",
                "qty": "45.00000000",
                "quoteQty": "8.19090000",
                "commission": "0.00000867",
                "commissionAsset": "BNB",
                "time": 1752133756571,
                "isBuyer": true,
                "isMaker": false,
                "isBestMatch": true
            },
            {
                "symbol": "DOGEUSDC",
                "id": 26739319,
                "orderId": 1291554287,
                "orderListId": -1,
                "price": "0.18186000",
                "qty": "45.00000000",
                "quoteQty": "8.18370000",
                "commission": "0.00000867",
                "commissionAsset": "BNB",
                "time": 1752133778333,
                "isBuyer": false,
                "isMaker": false,
                "isBestMatch": true
            }
        ]
        ```
        
    - Create 1 spot_buy record, 1 spot_sell record, and 1 fee record for each trade to `cex.binance.processed.trades`  as per below:
        - spot_buy records:
            - source = `cex.binance.raw.trades`
            - external_id = id
            - datetime = time
            - txn_type = “trade”
            - txn_subtype = “spot_buy”
            - email = mapped from query api key
            - wallet = “SPOT”
            - symbol = symbol
            - asset = baseAsset if isBuyer == true, else quoteAsset
            - amount = qty if isBuyer == true, else quoteQty
        - spot_sell records:
            - source = `cex.binance.raw.trades`
            - external_id = id
            - datetime = time
            - txn_type = “trade”
            - txn_subtype = “spot_sell”
            - email = mapped from query api key
            - wallet = “SPOT”
            - symbol = symbol
            - asset = quoteAsset * -1 if isBuyer == true, else baseAsset
            - amount = quoteQty if isBuyer == true, else qty
        - fee records
            - source = `cex.binance.raw.trades`
            - external_id = id
            - datetime = time
            - txn_type = “trade”
            - txn_subtype = “maker_fee” if isMaker = true, else “taker_fee”
            - email = mapped from query api key
            - wallet = “SPOT”
            - symbol = symbol
            - asset = commissionAsset
            - amount = commission * -1
    
    ---
    
    function `reconcile_spot(startDate, endDate, api_key)` :
    
    - for each `asset` in each `spot` balance in `cex.binance.processed.balances` of the `assetDate` and `endDate`
    - add all transaction
    - add all trades
    - returned: `cal_balance`