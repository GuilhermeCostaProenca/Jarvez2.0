import { type RoleAbilitiesPerLevel } from './RoleAbilitiesPerLevel';
export declare class RoleAbilitiesPerLevelFactory {
    static make<T extends Partial<RoleAbilitiesPerLevel>>(abilities: T): T & RoleAbilitiesPerLevel;
}
