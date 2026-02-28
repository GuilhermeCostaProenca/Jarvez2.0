import { type BuildingSheet } from '../Sheet';
import { Action, type ActionSubClassParams } from './Action';
export declare class ChooseRole extends Action<'chooseRole', BuildingSheet> {
    constructor(params: ActionSubClassParams<'chooseRole', BuildingSheet>);
    execute(): void;
    getDescription(): string;
}
