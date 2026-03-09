import { EquipmentName } from '../../EquipmentName';
import { EquipmentAlchemic } from '../EquipmentAlchemic';
import { EquipmentAlchemicCategory } from '../EquipmentAlchemicCategory';
export declare class Bomb extends EquipmentAlchemic {
    alchemicCategory: EquipmentAlchemicCategory;
    price: number;
    description: string;
    name: EquipmentName;
    isWieldable: boolean;
}
