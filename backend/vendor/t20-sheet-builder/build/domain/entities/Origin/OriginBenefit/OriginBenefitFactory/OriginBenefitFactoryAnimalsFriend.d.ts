import { type OriginBenefit } from '../OriginBenefit';
import { type SerializedOriginBenefitsAnimalsFriend } from '../SerializedOriginBenefit';
import { OriginBenefitFactory } from './OriginBenefitFactory';
export declare class OriginBenefitFactoryAnimalsFriend extends OriginBenefitFactory<SerializedOriginBenefitsAnimalsFriend, OriginBenefit<SerializedOriginBenefitsAnimalsFriend>> {
    makeFromSerialized(serialized: SerializedOriginBenefitsAnimalsFriend): OriginBenefit<SerializedOriginBenefitsAnimalsFriend>;
}
