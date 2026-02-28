import { PassiveEffect } from '../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import type { VersatileChoice } from './VersatileChoice';
export declare class VersatileEffect extends PassiveEffect {
    get description(): string;
    readonly choices: VersatileChoice[];
    constructor();
    addChoice(newChoice: VersatileChoice): void;
    apply(transaction: TransactionInterface): void;
}
