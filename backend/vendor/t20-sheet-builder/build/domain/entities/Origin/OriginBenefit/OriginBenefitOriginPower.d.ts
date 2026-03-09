import { type OriginPowerName } from '../../Power';
import type { OriginPowerInterface } from '../../Power/OriginPower/OriginPower';
import type { Transaction } from '../../Sheet/Transaction';
import { type TranslatableName } from '../../Translator';
import { OriginBenefit } from './OriginBenefit';
import { type OriginBenefits } from './OriginBenefits';
import { type SerializedOriginPowers } from './SerializedOriginBenefit';
export declare class OriginBenefitOriginPower<S extends SerializedOriginPowers> extends OriginBenefit<S> {
    readonly power: OriginPowerInterface<S>;
    name: OriginPowerName;
    constructor(power: OriginPowerInterface<S>);
    apply(transaction: Transaction, source: TranslatableName): void;
    validate(originBenefits: OriginBenefits): void;
    serialize(): S;
}
