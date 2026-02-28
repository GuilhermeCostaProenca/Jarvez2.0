import { PassiveEffect } from '../../../../Ability/PassiveEffect';
import { type TransactionInterface } from '../../../../Sheet/TransactionInterface';
import { type ArcanistPathWizardFocus } from './ArcanistPathWizardFocus';
export declare class ArcanistPathWizardFocusEffect extends PassiveEffect {
    readonly focus: ArcanistPathWizardFocus;
    get description(): string;
    constructor(focus: ArcanistPathWizardFocus);
    apply(transaction: TransactionInterface): void;
}
