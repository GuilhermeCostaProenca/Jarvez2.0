import { EquipmentAdventure } from '../../Inventory/Equipment/EquipmentAdventure/EquipmentAdventure';
import { EquipmentClothing } from '../../Inventory/Equipment/EquipmentClothing/EquipmentClothing';
import { GeneralPowerName } from '../../Power/GeneralPower/GeneralPowerName';
import { OriginPowerName } from '../../Power/OriginPower/OriginPowerName';
import { SkillName } from '../../Skill/SkillName';
import { Origin } from '../Origin';
import type { OriginBenefit } from '../OriginBenefit/OriginBenefit';
import { type SerializedOriginBenefitsAcolyte } from '../OriginBenefit/SerializedOriginBenefit';
import { OriginName } from '../OriginName';
import { type SerializedAcolyte } from '../SerializedOrigin';
export type SerializedChosenChurchMember = {
    name: OriginPowerName.churchMember;
};
export declare class Acolyte extends Origin<SerializedOriginBenefitsAcolyte, SerializedAcolyte> {
    static readonly originName = OriginName.acolyte;
    static equipments: string;
    static skills: SkillName[];
    static generalPowers: GeneralPowerName[];
    static originPower: OriginPowerName;
    readonly name = OriginName.acolyte;
    equipments: (EquipmentAdventure | EquipmentClothing)[];
    constructor(chosenBenefits: Array<OriginBenefit<SerializedOriginBenefitsAcolyte>>);
    serialize(): SerializedAcolyte;
}
