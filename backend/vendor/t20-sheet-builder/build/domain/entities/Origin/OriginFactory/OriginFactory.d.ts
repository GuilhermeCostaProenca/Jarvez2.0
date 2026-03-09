import { Acolyte } from '../Acolyte/Acolyte';
import { AnimalsFriend } from '../AnimalsFriend/AnimalsFriend';
import { OriginBenefitGeneralPower } from '../OriginBenefit/OriginBenefitGeneralPower';
import { OriginBenefitOriginPower } from '../OriginBenefit/OriginBenefitOriginPower';
import { OriginBenefitSkill } from '../OriginBenefit/OriginBenefitSkill';
import { type SerializedOriginBenefit } from '../OriginBenefit/SerializedOriginBenefit';
import { type SerializedOrigins, type SerializedSheetOrigin } from '../SerializedOrigin';
export declare class OriginFactory {
    static makeFromSerialized<T extends SerializedOrigins>(serialized: SerializedSheetOrigin<T>): AnimalsFriend | Acolyte;
    static makeBenefitsFromSerialized(serialized: SerializedOriginBenefit): OriginBenefitGeneralPower | OriginBenefitSkill | OriginBenefitOriginPower<import("../OriginBenefit/SerializedOriginBenefit").SerializedOriginPowers>;
}
