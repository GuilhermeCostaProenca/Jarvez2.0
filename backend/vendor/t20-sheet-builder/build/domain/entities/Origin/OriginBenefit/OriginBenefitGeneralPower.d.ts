import { type GeneralPowerName } from '../../Power';
import type { GeneralPowerInterface } from '../../Power/GeneralPower/GeneralPower';
import { type TransactionInterface } from '../../Sheet/TransactionInterface';
import { type TranslatableName } from '../../Translator';
import { OriginBenefit } from './OriginBenefit';
import { type OriginBenefits } from './OriginBenefits';
export type SerializedOriginBenefitGeneralPower = {
    type: 'generalPowers';
    name: GeneralPowerName;
};
export declare class OriginBenefitGeneralPower extends OriginBenefit<SerializedOriginBenefitGeneralPower> {
    readonly power: GeneralPowerInterface;
    name: GeneralPowerName;
    constructor(power: GeneralPowerInterface);
    serialize(): SerializedOriginBenefitGeneralPower;
    apply(transaction: TransactionInterface, source: TranslatableName): void;
    validate(originBenefits: OriginBenefits): void;
}
