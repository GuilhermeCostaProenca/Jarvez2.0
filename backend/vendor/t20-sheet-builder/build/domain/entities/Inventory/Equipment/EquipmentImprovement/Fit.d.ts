import { EquipmentImprovement } from './EquipmentImprovement';
import { EquipmentImprovementCategory } from './EquipmentImprovementCategory';
import { EquipmentImprovementName } from './EquipmentImprovementName';
export declare class Fit extends EquipmentImprovement {
    name: EquipmentImprovementName;
    description: string;
    category: EquipmentImprovementCategory;
}
