import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import { GeneralPower } from '../GeneralPower';
import { GeneralPowerGroup } from '../GeneralPowerGroup';
export declare abstract class TormentaPower extends GeneralPower {
    group: GeneralPowerGroup;
    addToSheet(transaction: TransactionInterface): void;
}
