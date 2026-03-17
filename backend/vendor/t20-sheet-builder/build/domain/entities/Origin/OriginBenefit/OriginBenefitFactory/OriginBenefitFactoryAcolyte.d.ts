import { type OriginBenefit } from '../OriginBenefit';
import { type SerializedOriginBenefitsAcolyte } from '../SerializedOriginBenefit';
import { OriginBenefitFactory } from './OriginBenefitFactory';
export declare class OriginBenefitFactoryAcolyte extends OriginBenefitFactory<SerializedOriginBenefitsAcolyte, OriginBenefit<SerializedOriginBenefitsAcolyte>> {
    makeFromSerialized(serialized: SerializedOriginBenefitsAcolyte): OriginBenefit<SerializedOriginBenefitsAcolyte>;
}
