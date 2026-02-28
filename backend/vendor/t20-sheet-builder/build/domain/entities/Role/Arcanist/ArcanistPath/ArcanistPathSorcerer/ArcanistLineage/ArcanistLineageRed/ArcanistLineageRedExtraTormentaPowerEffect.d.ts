import { PassiveEffect } from '../../../../../../Ability/PassiveEffect';
import { type TormentaPower } from '../../../../../../Power/GeneralPower/TormentaPower/TormentaPower';
import { type TransactionInterface } from '../../../../../../Sheet/TransactionInterface';
export declare class ArcanistLineageRedExtraTormentaPowerEffect extends PassiveEffect {
    readonly power: TormentaPower;
    get description(): string;
    constructor(power: TormentaPower);
    apply(transaction: TransactionInterface): void;
}
