import { type BuildingSheet } from '../Sheet';
import { Action, type ActionSubClassParams } from './Action';
export declare class ChooseOrigin extends Action<'chooseOrigin', BuildingSheet> {
    constructor(params: ActionSubClassParams<'chooseOrigin', BuildingSheet>);
    execute(): void;
    getDescription(): string;
}
