import { OffensiveWeapon } from '../OffensiveWeapon';
import { type ExoticWeaponName } from './ExoticWeaponName';
export declare abstract class ExoticWeapon extends OffensiveWeapon {
    abstract name: ExoticWeaponName;
    constructor();
}
