import type { Proficiency } from '../../../../../Sheet/Proficiency';
import { EquipmentImprovementCategory } from '../../../EquipmentImprovement/EquipmentImprovementCategory';
import { DefensiveWeapon } from '../DefensiveWeapon';
import { type ArmorName } from './ArmorName';
export declare abstract class Armor<T extends ArmorName = ArmorName> extends DefensiveWeapon<T> {
    readonly proficiency: Proficiency.lightArmor | Proficiency.heavyArmor;
    readonly categoryForImprovement: EquipmentImprovementCategory;
    get isWieldable(): boolean;
    constructor(proficiency: Proficiency.lightArmor | Proficiency.heavyArmor);
}
